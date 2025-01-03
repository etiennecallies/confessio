from datetime import timedelta
from typing import Optional

from django.utils import timezone

from home.models import Pruning, Website, Parsing, ParsingModeration, Church
from home.utils.hash_utils import hash_string_to_hex
from scraping.parse.parse_with_llm import parse_with_llm, get_llm_model, get_prompt_template
from scraping.parse.schedules import SchedulesList
from scraping.refine.refine_content import remove_link_from_html

TRUNCATION_LENGTH = 32
MAX_LENGTH_FOR_PARSING = 3000


##############
# TRUNCATION #
##############

def get_truncated_line(line: str) -> str:
    truncated_line = remove_link_from_html(line)[:TRUNCATION_LENGTH]
    return f'[{truncated_line}...]'


def get_truncated_html(pruning: Pruning) -> str:
    lines = pruning.extracted_html.split('<br>\n')

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


###############
# CHURCH DESC #
###############

def get_id_by_value(church_desc: str, church_desc_by_id: dict[int, str]) -> int:
    for index, desc in church_desc_by_id.items():
        if desc == church_desc:
            return int(index)

    raise ValueError(f'Church description {church_desc} not found in church_desc_by_id')


def get_church_by_id(parsing: Parsing, website: Website) -> dict[int, Church]:
    church_by_id = {}
    for parish in website.parishes.all():
        for church in parish.churches.all():
            church_id = get_id_by_value(church.get_desc(), parsing.church_desc_by_id)
            church_by_id[church_id] = church

    return church_by_id


########################
# PARSING MANIPULATION #
########################

BASE_FIELDS = {'church_id', 'is_cancellation', 'start_time_iso8601', 'end_time_iso8601'}


def get_existing_parsing(truncated_html: str,
                         church_desc_by_id: dict[int, str]) -> Optional[Parsing]:
    try:
        return Parsing.objects.filter(truncated_html=truncated_html,
                                      church_desc_by_id=church_desc_by_id).get()
    except Parsing.DoesNotExist:
        return None


def get_parsing_schedules_list(parsing: Parsing) -> Optional[SchedulesList]:
    schedules_list_as_dict = parsing.human_json or parsing.llm_json
    if schedules_list_as_dict is None:
        return None

    return SchedulesList(**schedules_list_as_dict)


##############
# MODERATION #
##############

def add_necessary_parsing_moderation(parsing: Parsing):
    if not parsing_needs_moderation(parsing):
        return

    if parsing.llm_json is not None and parsing.human_json == parsing.llm_json:
        return

    category = ParsingModeration.Category.NEW_SCHEDULES
    add_parsing_moderation(parsing, category)


def add_parsing_moderation(parsing: Parsing, category: ParsingModeration.Category):
    try:
        parsing_moderation = ParsingModeration.objects.filter(parsing=parsing,
                                                              category=category).get()
        parsing_moderation.validated_at = None
        parsing_moderation.validated_by = None
        parsing_moderation.save()
    except ParsingModeration.DoesNotExist:
        parsing_moderation = ParsingModeration(
            parsing=parsing,
            category=category,
        )
        parsing_moderation.save()


def remove_parsing_moderation(parsing: Parsing, category: ParsingModeration.Category):
    ParsingModeration.objects.filter(parsing=parsing, category=category).delete()


def parsing_needs_moderation(parsing: Parsing):
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
        if not any(is_eligible_to_parsing(w) for w in parsing_moderation.parsing.get_websites()):
            parsing_moderation.delete()
            counter += 1

    return counter


###########################
# Website & Pruning links #
###########################

def has_parsing_a_matching_website(parsing: Parsing) -> bool:
    for website in parsing.get_websites():
        if parsing.match_website(website):
            return True

    return False


def unlink_website_from_existing_parsing_for_pruning(pruning: Pruning):
    parsings = Parsing.objects.filter(prunings=pruning).all()

    for parsing in parsings:
        if not has_parsing_a_matching_website(parsing):
            print(f'deleting not validated moderation for parsing {parsing} since it has no '
                  f'website any more')
            ParsingModeration.objects.filter(parsing=parsing, validated_at__isnull=True).delete()


def unlink_pruning_from_existing_parsing(pruning: Pruning):
    parsings = Parsing.objects.filter(prunings=pruning).all()

    for parsing in parsings:
        if parsing.truncated_html != get_truncated_html(pruning):
            print(f'deleting not validated moderation for parsing {parsing} since it has no '
                  f'pruning any more')
            parsing.prunings.remove(pruning)
            ParsingModeration.objects.filter(parsing=parsing, validated_at__isnull=True).delete()


########
# MAIN #
########

def parse_pruning_for_website(pruning: Pruning, website: Website, force_parse: bool = False):
    if not is_eligible_to_parsing(website):
        print(f'website {website} not eligible to parsing')
        return

    truncated_html = get_truncated_html(pruning)
    if not truncated_html:
        print(f'No truncated html for pruning {pruning}')
        return

    if len(truncated_html) > MAX_LENGTH_FOR_PARSING:
        print(f'No parsing above {MAX_LENGTH_FOR_PARSING}, got {len(truncated_html)}')
        return

    truncated_html_hash = hash_string_to_hex(truncated_html)
    church_desc_by_id = website.get_church_desc_by_id()

    llm_model = get_llm_model()
    prompt_template = get_prompt_template()
    prompt_template_hash = hash_string_to_hex(prompt_template)

    # check the parsing does not already exist
    parsing = get_existing_parsing(truncated_html, church_desc_by_id)
    if not force_parse and parsing \
            and parsing.llm_model == llm_model \
            and parsing.prompt_template_hash == prompt_template_hash:

        # Check if parsing is already linked to the pruning
        if not parsing.prunings.filter(pk=pruning.pk).exists():
            parsing.prunings.add(pruning)

        print(f'Parsing already exists for pruning {pruning}')
        return

    print(f'parsing {pruning} for website {website}')
    schedules_list, llm_error_detail = parse_with_llm(truncated_html, church_desc_by_id,
                                                      llm_model, prompt_template)
    llm_json = schedules_list.model_dump() if schedules_list else None

    if parsing:
        parsing.llm_json = llm_json
        parsing.llm_model = llm_model
        parsing.prompt_template_hash = prompt_template_hash
        parsing.llm_error_detail = llm_error_detail
        parsing.save()
    else:
        unlink_website_from_existing_parsing_for_pruning(pruning)
        unlink_pruning_from_existing_parsing(pruning)

        parsing = Parsing(
            truncated_html=truncated_html,
            truncated_html_hash=truncated_html_hash,
            church_desc_by_id=church_desc_by_id,
            llm_json=llm_json,
            llm_model=llm_model,
            prompt_template_hash=prompt_template_hash,
            llm_error_detail=llm_error_detail,
        )
        parsing.save()

    parsing.prunings.add(pruning)
    if llm_error_detail:
        add_parsing_moderation(parsing, ParsingModeration.Category.LLM_ERROR)
    else:
        remove_parsing_moderation(parsing, ParsingModeration.Category.LLM_ERROR)
        add_necessary_parsing_moderation(parsing)
