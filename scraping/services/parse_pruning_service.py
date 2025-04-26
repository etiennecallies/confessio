import re
from datetime import timedelta

from django.db.models.functions import Now
from django.utils import timezone

from home.models import Pruning, Website, Parsing, ParsingModeration, Page
from home.utils.async_utils import run_in_sync
from home.utils.hash_utils import hash_string_to_hex
from home.utils.log_utils import info
from scraping.parse.llm_client import LLMClientInterface
from scraping.parse.parse_with_llm import parse_with_llm, get_prompt_template, get_llm_client
from scraping.parse.schedules import SchedulesList
from scraping.refine.refine_content import remove_link_from_html
from scraping.services.index_events_service import index_events_for_website
from scraping.services.parsing_service import get_existing_parsing

TRUNCATION_LENGTH = 32
MAX_LENGTH_FOR_PARSING = 5000


##############
# TRUNCATION #
##############

def get_truncated_line(line: str) -> str:
    truncated_line = remove_link_from_html(line)[:TRUNCATION_LENGTH]
    return f'[{truncated_line}...]'


def get_truncated_html(pruning: Pruning) -> str:
    extracted_html = str(re.sub(r"\n\s*", "", pruning.extracted_html))
    lines = extracted_html.split('<br>')

    truncated_lines = []
    last_index = None
    for index in pruning.pruned_indices:
        if last_index is not None and index != last_index + 1:
            truncated_lines.append(get_truncated_line(lines[last_index + 1]))
            if index - 1 > last_index + 1:
                if index - 2 > last_index + 1:
                    truncated_lines.append('[...]')
                truncated_lines.append(get_truncated_line(lines[index - 1]))
        truncated_lines.append(lines[index])
        last_index = index

    return '<br>'.join(truncated_lines)


##############
# MODERATION #
##############

def add_necessary_parsing_moderation(parsing: Parsing, website: Website):
    category = get_category(parsing)
    needs_moderation = parsing_needs_moderation(parsing)

    # 1. we remove moderation of other category
    remove_parsing_moderation_of_other_category(parsing, category)

    # 2. we add moderation
    add_parsing_moderation(parsing, category, needs_moderation, website)


def add_parsing_moderation(parsing: Parsing, category: ParsingModeration.Category,
                           needs_moderation: bool, website: Website):
    try:
        parsing_moderation = ParsingModeration.objects.filter(parsing=parsing,
                                                              category=category).get()
        if needs_moderation:
            if parsing_moderation.validated_at is not None \
                    or parsing_moderation.validated_by is not None:
                parsing_moderation.validated_at = None
                parsing_moderation.validated_by = None
                parsing_moderation.save()
    except ParsingModeration.DoesNotExist:
        parsing_moderation = ParsingModeration(
            parsing=parsing,
            category=category,
            validated_at=None if needs_moderation else Now(),
            diocese=website.get_diocese(),
        )
        parsing_moderation.save()


def remove_parsing_moderation_of_other_category(parsing: Parsing,
                                                category: ParsingModeration.Category):
    ParsingModeration.objects.filter(parsing=parsing).exclude(category=category).delete()


def get_category(parsing: Parsing) -> ParsingModeration.Category:
    if parsing.llm_error_detail:
        return ParsingModeration.Category.LLM_ERROR

    if parsing.human_json is not None and parsing.human_json != parsing.llm_json:
        return ParsingModeration.Category.SCHEDULES_DIFFER

    return ParsingModeration.Category.NEW_SCHEDULES


def parsing_needs_moderation(parsing: Parsing):
    if parsing.human_json is not None and parsing.human_json == parsing.llm_json:
        return False

    if parsing.human_json is not None and parsing.human_json != parsing.llm_json:
        if ParsingModeration.objects.filter(
                parsing=parsing,
                category=ParsingModeration.Category.SCHEDULES_DIFFER,
                validated_at__isnull=False
        ).exists():
            return False

        return True

    for pruning in parsing.prunings.all():
        for scraping in pruning.scrapings.all():
            page = scraping.page

            # If website has been marked as unreliable, we don't want to moderate it
            if page.website.unreliability_reason:
                break

            # if page has been validated less than three times or more than one year ago
            # and if website has been validated less than seven times or more than one year ago
            if (
                page.parsing_validation_counter < 2
                or page.parsing_last_validated_at is None
                or page.parsing_last_validated_at < (timezone.now() - timedelta(days=365))
            ) and (
                page.website.parsing_validation_counter < 6
                or page.website.parsing_last_validated_at is None
                or page.website.parsing_last_validated_at < (timezone.now() - timedelta(days=365))
            ):
                return True

    return False


#########################
# MODERATION VALIDATION #
#########################

class ParsingValidationError(Exception):
    pass


def on_parsing_human_validation(parsing_moderation: ParsingModeration):
    parsing = parsing_moderation.parsing
    if parsing.human_json is None:
        if parsing.llm_json is None:
            raise ParsingValidationError(
                'No human nor LLM json for parsing, can not be validated'
            )

        set_human_json(parsing)

    increment_counters_of_parsing(parsing)


def set_human_json(parsing: Parsing):
    parsing.human_json = parsing.llm_json
    parsing.save()
    re_index_related_website(parsing)


def re_index_related_website(parsing: Parsing):
    if parsing.website:
        index_events_for_website(parsing.website)


############
# COUNTERS #
############

def reset_counters_of_parsing(parsing: Parsing):
    websites_to_update = set()
    for pruning in parsing.prunings.all():
        for scraping in pruning.scrapings.all():
            page = scraping.page
            page.parsing_validation_counter = -1
            page.save()
            websites_to_update.add(page.website)

    for website in websites_to_update:
        website.parsing_validation_counter = -1
        website.save()


def increment_counters_of_parsing(parsing: Parsing):
    websites_to_update = set()
    for pruning in parsing.prunings.all():
        for scraping in pruning.scrapings.all():
            page = scraping.page
            page.parsing_validation_counter += 1
            page.save()
            websites_to_update.add(page.website)

    for website in websites_to_update:
        website.parsing_validation_counter += 1
        website.save()


####################
# MODERATION CLEAN #
####################

def is_eligible_to_parsing(website: Website):
    return website.unreliability_reason != Website.UnreliabilityReason.SCHEDULE_IN_IMAGE


def clean_parsing_moderations() -> int:
    counter = 0
    for parsing_moderation in ParsingModeration.objects.filter(validated_at__isnull=True).all():
        website = parsing_moderation.parsing.website
        if not website or not is_eligible_to_parsing(website):
            parsing_moderation.delete()
            counter += 1

    return counter


#################################
# WEBSITE <-> PARSING relations #
#################################

def check_website_parsing_relations(website: Website) -> bool:
    direct_parsings = {p.uuid for p in Parsing.objects.filter(website=website).all()}
    indirect_parsings = {
        parsing.uuid
        for parsing in [
            pruning.get_parsing(website)
            for pruning in Pruning.objects.filter(scrapings__page__website=website).all()
        ] if parsing
    }
    return direct_parsings == indirect_parsings


def debug_website_parsing_relations(website: Website):
    info(f'Website {website.name} {website.uuid} parsing relations:')
    info()
    info('Direct parsings:')
    for parsing in Parsing.objects.filter(website=website).all():
        info(f' - Parsing {parsing.uuid}')
        for pruning in parsing.prunings.all():
            info(f'  - Pruning {pruning.uuid}')
            for scraping in pruning.scrapings.all():
                info(f'   - Scraping {scraping.uuid}')
                page = scraping.page
                info(f'    - Page {page.uuid} {page.url}')
                info(f'     - Website {page.website.name} {page.website.uuid}')

    info('Indirect parsings:')
    for page in Page.objects.filter(website=website).all():
        info(f' - Page {page.uuid} {page.url}')
        scraping = page.scraping
        info(f'  - Scraping {scraping.uuid}')
        for pruning in scraping.prunings.all():
            info(f'   - Pruning {pruning.uuid}')
            parsing = pruning.get_parsing(website)
            if parsing:
                info(f'    - Parsing {parsing.uuid}')
                if parsing.website:
                    info(f'     - Website {parsing.website.name} {parsing.website.uuid}')
                else:
                    info(f'     - No website for parsing {parsing.uuid}')
            else:
                info(f'    - No parsing for pruning {pruning.uuid}')
    info()


###########################
# Website & Pruning links #
###########################

def unlink_website_from_parsings_except_church_desc_by_id(website: Website,
                                                          church_desc_by_id: dict[int, str]):
    """
    Handle change of church_desc_by_id for a website
    """
    parsings = Parsing.objects.filter(website=website)\
        .exclude(church_desc_by_id=church_desc_by_id).all()

    for parsing in parsings:
        info(f'parsing {parsing.uuid} has changed church_desc_by_id, unlinking website '
             f'{website.uuid} and all prunings')
        parsing.prunings.clear()
        unlink_website_from_parsing(parsing)


def unlink_website_from_parsing(parsing: Parsing):
    if not parsing.website:
        return

    website = parsing.website

    # unlink website from parsing
    parsing.website = None
    parsing.save()

    # re-index events for the website
    index_events_for_website(website)

    info(f'deleting not validated moderation for parsing {parsing} since it has no '
         f'website any more')
    ParsingModeration.objects.filter(parsing=parsing, validated_at__isnull=True).delete()


def unlink_pruning_from_parsing(parsing: Parsing, pruning: Pruning):
    parsing.prunings.remove(pruning)
    if parsing.website:
        if not parsing.prunings.filter(scrapings__page__website=parsing.website).exists():
            info(f'parsing {parsing.uuid} has no more prunings for website {parsing.website.uuid}')
            unlink_website_from_parsing(parsing)


def unlink_pruning_from_parsings_except_truncated_html_hash(pruning: Pruning,
                                                            truncated_html_hash: str):
    """
    Handle change of truncated_html for a pruning
    """
    parsings = Parsing.objects.filter(prunings=pruning)\
        .exclude(truncated_html_hash=truncated_html_hash).all()

    for parsing in parsings:
        info(f'unlinking pruning {pruning.uuid} from parsing {parsing.uuid} '
             f'because of changed truncated html')
        unlink_pruning_from_parsing(parsing, pruning)


def unlink_orphan_pruning_for_website(pruning: Pruning, website: Website):
    """
    Handle a pruning that disappeared for a website
    """
    parsings = Parsing.objects.filter(prunings=pruning, website=website).all()

    for parsing in parsings:
        info(f'unlinking parsing {parsing.uuid} from orphan pruning {pruning.uuid}')
        unlink_pruning_from_parsing(parsing, pruning)


########
# MAIN #
########

def prepare_parsing(
        pruning: Pruning, website: Website, force_parse: bool = False
) -> None | tuple[str, str, dict[int, str], LLMClientInterface, str, str, Parsing | None]:
    if not is_eligible_to_parsing(website):
        info(f'website {website} not eligible to parsing')
        return None

    truncated_html = get_truncated_html(pruning)
    truncated_html_hash = hash_string_to_hex(truncated_html) if truncated_html else None
    unlink_pruning_from_parsings_except_truncated_html_hash(pruning, truncated_html_hash)

    church_desc_by_id = website.get_church_desc_by_id()
    unlink_website_from_parsings_except_church_desc_by_id(website, church_desc_by_id)

    if not truncated_html:
        info(f'No truncated html for pruning {pruning}')
        return None

    llm_client = get_llm_client()
    prompt_template = get_prompt_template()
    prompt_template_hash = hash_string_to_hex(prompt_template)

    # check the parsing does not already exist
    parsing = get_existing_parsing(truncated_html_hash, church_desc_by_id)
    if not force_parse and parsing \
            and parsing.llm_provider == llm_client.get_provider() \
            and parsing.llm_model == llm_client.get_model() \
            and parsing.prompt_template_hash == prompt_template_hash:

        # Check if parsing is already linked to the pruning
        if not parsing.prunings.filter(pk=pruning.pk).exists():
            parsing.prunings.add(pruning)

        # Check if website is already linked to the pruning
        if not parsing.website:
            parsing.website = website
            parsing.save()
            index_events_for_website(website)

        # Adding necessary moderation if missing
        add_necessary_parsing_moderation(parsing, website)

        info(f'Parsing already exists for pruning {pruning}')
        return None

    return truncated_html, truncated_html_hash, church_desc_by_id, llm_client, prompt_template, \
        prompt_template_hash, parsing


async def parse_pruning_for_website(pruning: Pruning, website: Website,
                                    force_parse: bool = False):
    parsing_preparation = await run_in_sync(prepare_parsing, pruning, website, force_parse)
    if not parsing_preparation:
        return

    truncated_html, truncated_html_hash, church_desc_by_id, llm_client, prompt_template, \
        prompt_template_hash, parsing = parsing_preparation

    if len(truncated_html) > MAX_LENGTH_FOR_PARSING:
        info(f'No parsing above {MAX_LENGTH_FOR_PARSING}, got {len(truncated_html)}')
        schedules_list, llm_error_detail = None, "Truncated html too long"
    else:
        info(f'parsing {pruning} for website {website}')
        schedules_list, llm_error_detail = await parse_with_llm(truncated_html, church_desc_by_id,
                                                                prompt_template, llm_client)

    await run_in_sync(save_parsing, parsing, pruning, website, truncated_html,
                      truncated_html_hash, church_desc_by_id, llm_client, prompt_template_hash,
                      llm_error_detail, schedules_list)


def save_parsing(parsing: Parsing | None, pruning: Pruning, website: Website,
                 truncated_html: str, truncated_html_hash: str,
                 church_desc_by_id: dict[int, str], llm_client: LLMClientInterface,
                 prompt_template_hash: str, llm_error_detail: str | None,
                 schedules_list: SchedulesList | None):
    llm_json = schedules_list.model_dump() if schedules_list else None

    if parsing:
        parsing.website = website
        parsing.llm_json = llm_json
        parsing.llm_provider = llm_client.get_provider()
        parsing.llm_model = llm_client.get_model()
        parsing.prompt_template_hash = prompt_template_hash
        parsing.llm_error_detail = llm_error_detail
        parsing.save()
    else:
        parsing = Parsing(
            website=website,
            truncated_html=truncated_html,
            truncated_html_hash=truncated_html_hash,
            church_desc_by_id=church_desc_by_id,
            llm_json=llm_json,
            llm_provider=llm_client.get_provider(),
            llm_model=llm_client.get_model(),
            prompt_template_hash=prompt_template_hash,
            llm_error_detail=llm_error_detail,
        )
        parsing.save()

    parsing.prunings.add(pruning)
    add_necessary_parsing_moderation(parsing, website)
    index_events_for_website(website)
