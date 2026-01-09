import asyncio
import re
from dataclasses import dataclass
from datetime import timedelta

from background_task import background
from background_task.tasks import TaskSchedule
from django.db.models.functions import Now
from django.utils import timezone

from home.models import Pruning, Website, Parsing, ParsingModeration, Page, Image, Log, Church
from home.utils.hash_utils import hash_string_to_hex
from home.utils.list_utils import get_desc_by_id
from home.utils.log_utils import info, start_log_buffer, get_log_buffer
from scheduling.models import Scheduling
from scheduling.services.scheduling_service import get_scheduling_parsings, get_websites_of_parsing
from scraping.parse.llm_client import LLMClientInterface
from scraping.parse.parse_with_llm import parse_with_llm, get_prompt_template, get_llm_client
from scraping.parse.schedules import SchedulesList, SCHEDULES_LIST_VERSION
from scraping.refine.refine_content import stringify_html
from scraping.services.parsing_service import get_existing_parsing

TRUNCATION_LENGTH = 32
MAX_LENGTH_FOR_PARSING = 15000


##############
# TRUNCATION #
##############

def get_truncated_line(line: str) -> str:
    truncated_line = stringify_html(line)[:TRUNCATION_LENGTH]
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


####################
# MODERATION CLEAN #
####################

def clean_parsing_moderations() -> int:
    counter = 0
    for parsing_moderation in ParsingModeration.objects.filter(validated_at__isnull=True).all():
        if not get_websites_of_parsing(parsing_moderation.parsing):
            parsing_moderation.delete()
            counter += 1

    return counter


#################################
# WEBSITE <-> PARSING relations #
#################################

def check_website_parsing_relations(website: Website, scheduling: Scheduling) -> bool:
    direct_parsings = get_scheduling_parsings(scheduling)
    indirect_parsings = {
        parsing.uuid
        for parsing in [
            pruning.get_parsing(website)
            for pruning in Pruning.objects.filter(scrapings__page__website=website).all()
        ] if parsing
    } | {
        parsing.uuid
        for parsing in [
            pruning.get_parsing(website)
            for pruning in Pruning.objects.filter(images__website=website).all()
        ] if parsing
    }
    direct_parsings_uuid = {parsing.uuid for parsing in direct_parsings}
    indirect_parsings_uuid = {parsing_uuid for parsing_uuid in indirect_parsings}
    return direct_parsings_uuid == indirect_parsings_uuid


def debug_website_parsing_relations(website: Website, scheduling: Scheduling) -> None:
    info(f'Website {website.name} {website.uuid} parsing relations:')
    info()
    info('Direct parsings:')
    for parsing in get_scheduling_parsings(scheduling):
        info(f' - Parsing {parsing.uuid}')
        for pruning in parsing.prunings.all():
            info(f'  - Pruning {pruning.uuid}')
            for scraping in pruning.scrapings.all():
                info(f'   - Scraping {scraping.uuid}')
                page = scraping.page
                info(f'    - Page {page.uuid} {page.url}')
                info(f'     - Website {page.website.name} {page.website.uuid}')
            for image in pruning.images.all():
                info(f'   - Image {image.uuid}')
                info(f'    - Website {image.website.name} {image.website.uuid}')

    info('Indirect parsings (page):')
    for page in Page.objects.filter(website=website).all():
        info(f' - Page {page.uuid} {page.url}')
        scraping = page.scraping
        info(f'  - Scraping {scraping.uuid}')
        for pruning in scraping.prunings.all():
            debug_pruning(pruning, website)
    info('Indirect parsings (image):')
    for image in Image.objects.filter(website=website).all():
        info(f' - Image {image.uuid}')
        for pruning in image.prunings.all():
            debug_pruning(pruning, website)
    info()


def debug_pruning(pruning: Pruning, website: Website) -> None:
    info(f'   - Pruning {pruning.uuid}')
    parsing = pruning.get_parsing(website)
    if parsing:
        info(f'    - Parsing {parsing.uuid}')
        websites = get_websites_of_parsing(parsing)
        if websites:
            for website in websites:
                info(f'     - Website {website.name} {website.uuid}')
        else:
            info(f'     - No website for parsing {parsing.uuid}')
    else:
        info(f'    - No parsing for pruning {pruning.uuid}')


###########################
# Pruning links #
###########################

def unlink_pruning_from_parsings_except_church_desc_by_id(website: Website,
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
        remove_useless_moderation_for_parsing(parsing)


def remove_useless_moderation_for_parsing(parsing: Parsing):
    if get_websites_of_parsing(parsing):
        return

    info(f'deleting not validated moderation for parsing {parsing} since it has no '
         f'website any more')
    ParsingModeration.objects.filter(parsing=parsing, validated_at__isnull=True).delete()


def unlink_pruning_from_parsing(parsing: Parsing, pruning: Pruning):
    parsing.prunings.remove(pruning)
    remove_useless_moderation_for_parsing(parsing)


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
        info(f'unlinking parsing {parsing.uuid} with website {website.uuid} '
             f'from orphan pruning {pruning.uuid}')
        unlink_pruning_from_parsing(parsing, pruning)


########
# MAIN #
########

@dataclass
class ParsingPreparation:
    truncated_html: str
    truncated_html_hash: str
    church_desc_by_id: dict[int, str]
    llm_client: LLMClientInterface
    prompt_template: str
    prompt_template_hash: str
    parsing: Parsing | None
    website: Website  # TODO remove website link


def prepare_parsing(
        pruning: Pruning, website: Website,
        churches: list[Church],
        force_parse: bool = False
) -> None | ParsingPreparation:
    truncated_html = get_truncated_html(pruning)
    truncated_html_hash = hash_string_to_hex(truncated_html) if truncated_html else None
    unlink_pruning_from_parsings_except_truncated_html_hash(pruning, truncated_html_hash)

    church_desc_by_id = get_desc_by_id([church.get_desc() for church in churches])
    unlink_pruning_from_parsings_except_church_desc_by_id(website, church_desc_by_id)

    if not truncated_html:
        info(f'No truncated html for pruning {pruning}, website {website.uuid}')
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

        # Adding necessary moderation if missing
        add_necessary_parsing_moderation(parsing, website)

        info(f'Parsing already exists for pruning {pruning}, website {website.uuid},'
             f' parsing {parsing.uuid}')
        return None

    return ParsingPreparation(truncated_html, truncated_html_hash, church_desc_by_id, llm_client,
                              prompt_template, prompt_template_hash, parsing, website)


def prepare_reparsing(parsing: Parsing) -> ParsingPreparation:
    truncated_html = parsing.truncated_html
    truncated_html_hash = parsing.truncated_html_hash
    church_desc_by_id = parsing.church_desc_by_id

    llm_client = get_llm_client()
    prompt_template = get_prompt_template()
    prompt_template_hash = hash_string_to_hex(prompt_template)

    return ParsingPreparation(truncated_html, truncated_html_hash, church_desc_by_id, llm_client,
                              prompt_template, prompt_template_hash, parsing, parsing.website)


@background(queue='main', schedule=TaskSchedule(priority=3))
def worker_parse_pruning_for_website(pruning_uuid: str, website_uuid: str, force_parse: bool):
    try:
        pruning = Pruning.objects.get(uuid=pruning_uuid)
        website = Website.objects.get(uuid=website_uuid)
    except (Pruning.DoesNotExist, Website.DoesNotExist) as e:
        info(f'Pruning {pruning_uuid} or Website {website_uuid} does not exist: {e}')
        return

    start_log_buffer()
    info(f'worker_parse_pruning_for_website: parsing {pruning_uuid} for website {website_uuid}')
    do_parse_pruning_for_website(pruning, website, website.get_churches(), force_parse)

    buffer_value = get_log_buffer()
    log = Log(type=Log.Type.PARSING,
              website=website,
              content=buffer_value,
              status=Log.Status.DONE)
    log.save()


def do_parse_pruning_for_website(pruning: Pruning, website: Website,
                                 churches: list[Church],
                                 force_parse: bool = False):
    parsing_preparation = prepare_parsing(pruning, website, churches, force_parse)
    if not parsing_preparation:
        return

    parse_parsing_preparation(parsing_preparation)


def parse_parsing_preparation(parsing_preparation: ParsingPreparation):
    truncated_html = parsing_preparation.truncated_html

    if len(truncated_html) > MAX_LENGTH_FOR_PARSING:
        info(f'No parsing above {MAX_LENGTH_FOR_PARSING}, got {len(truncated_html)},'
             f' website {parsing_preparation.website.uuid}')
        schedules_list, llm_error_detail = None, "Truncated html too long"
    else:
        info(f'parsing website {parsing_preparation.website} with '
             f'hash {parsing_preparation.truncated_html_hash}')
        schedules_list, llm_error_detail = asyncio.run(
            parse_with_llm(truncated_html,
                           parsing_preparation.church_desc_by_id,
                           parsing_preparation.prompt_template,
                           parsing_preparation.llm_client)
        )

    save_parsing(parsing_preparation, schedules_list, llm_error_detail)


def save_parsing(parsing_preparation: ParsingPreparation,
                 schedules_list: SchedulesList | None,
                 llm_error_detail: str | None):
    llm_json = schedules_list.model_dump(mode="json") if schedules_list else None
    parsing = parsing_preparation.parsing
    llm_client = parsing_preparation.llm_client

    if parsing:
        parsing.website = parsing_preparation.website
        parsing.llm_json = llm_json
        parsing.llm_json_version = SCHEDULES_LIST_VERSION
        parsing.llm_provider = llm_client.get_provider()
        parsing.llm_model = llm_client.get_model()
        parsing.prompt_template_hash = parsing_preparation.prompt_template_hash
        parsing.llm_error_detail = llm_error_detail
        parsing.save()
    else:
        parsing = Parsing(
            website=parsing_preparation.website,
            truncated_html=parsing_preparation.truncated_html,
            truncated_html_hash=parsing_preparation.truncated_html_hash,
            church_desc_by_id=parsing_preparation.church_desc_by_id,
            llm_json=llm_json,
            llm_json_version=SCHEDULES_LIST_VERSION,
            llm_provider=llm_client.get_provider(),
            llm_model=llm_client.get_model(),
            prompt_template_hash=parsing_preparation.prompt_template_hash,
            llm_error_detail=llm_error_detail,
        )
        parsing.save()

    add_necessary_parsing_moderation(parsing, parsing_preparation.website)
