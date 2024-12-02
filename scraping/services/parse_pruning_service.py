from datetime import timedelta
from typing import Optional

from django.forms import model_to_dict
from django.utils import timezone
from pydantic import ValidationError

from home.models import Pruning, Website, Parsing, Schedule, ParsingModeration, Church, \
    OneOffSchedule, RegularSchedule
from home.utils.hash_utils import hash_string_to_hex
from scraping.parse.parse_with_llm import parse_with_llm, get_llm_model, get_prompt_template
from scraping.parse.schedules import SchedulesList, ScheduleItem
from scraping.refine.refine_content import remove_link_from_html

TRUNCATION_LENGTH = 10
MAX_LENGTH_FOR_PARSING = 3000


##############
# TRUNCATION #
##############

def get_truncated_html(pruning: Pruning) -> str:
    lines = pruning.extracted_html.split('<br>\n')

    truncated_lines = []
    last_index = -1
    for index in pruning.pruned_indices:
        if index != last_index + 1:
            truncated_line = remove_link_from_html(lines[last_index + 1])[:TRUNCATION_LENGTH]
            truncated_lines.append(f'[{truncated_line}...]')
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


def schedule_item_from_schedule(schedule: Schedule) -> ScheduleItem:
    exclude_fields = {'id', 'schedule'}

    schedule_dict = model_to_dict(schedule, fields=BASE_FIELDS)
    schedule_dict['date_rule'] = model_to_dict(schedule, exclude=BASE_FIELDS | exclude_fields)

    return ScheduleItem(**schedule_dict)


def get_parsing_schedules_list(parsing: Parsing) -> Optional[SchedulesList]:
    if parsing.error_detail:
        return None

    try:
        return SchedulesList(
            schedules=list(map(schedule_item_from_schedule, parsing.get_schedules())),
            possible_by_appointment=parsing.possible_by_appointment,
            is_related_to_mass=parsing.is_related_to_mass,
            is_related_to_adoration=parsing.is_related_to_adoration,
            is_related_to_permanence=parsing.is_related_to_permanence,
            will_be_seasonal_events=parsing.will_be_seasonal_events,
        )
    except ValidationError as e:
        print('ValidationError when creating SchedulesList from existing parsing')
        print(e)
        return None


def save_schedule_list(parsing: Parsing, schedules_list: Optional[SchedulesList]):
    if schedules_list is None:
        return

    for schedule in parsing.get_schedules():
        schedule.delete()

    for schedule_item in schedules_list.schedules:
        if schedule_item.is_one_off_rule():
            schedule = OneOffSchedule(
                parsing=parsing,
                **schedule_item.model_dump(include=BASE_FIELDS),
                **schedule_item.date_rule.model_dump()
            )
        elif schedule_item.is_regular_rule():
            schedule = RegularSchedule(
                parsing=parsing,
                **schedule_item.model_dump(include=BASE_FIELDS),
                **schedule_item.date_rule.model_dump()
            )
        else:
            raise ValueError('Unknown schedule type')
        schedule.save()

    parsing.possible_by_appointment = schedules_list.possible_by_appointment
    parsing.is_related_to_mass = schedules_list.is_related_to_mass
    parsing.is_related_to_adoration = schedules_list.is_related_to_adoration
    parsing.is_related_to_permanence = schedules_list.is_related_to_permanence
    parsing.will_be_seasonal_events = schedules_list.will_be_seasonal_events
    parsing.save()


##############
# MODERATION #
##############

def add_necessary_parsing_moderation(parsing: Parsing, schedules_list: Optional[SchedulesList]):
    if not parsing_needs_moderation(parsing):
        return

    category = ParsingModeration.Category.NEW_SCHEDULES
    try:
        parsing_moderation = ParsingModeration.objects.filter(parsing=parsing,
                                                              category=category).get()
        if (schedules_list is None
                or parsing_moderation.validated_schedules_list != schedules_list.model_dump()):
            parsing_moderation.validated_at = None
            parsing_moderation.validated_by = None
            parsing_moderation.save()
    except ParsingModeration.DoesNotExist:
        parsing_moderation = ParsingModeration(
            parsing=parsing,
            category=category,
        )
        parsing_moderation.save()


def update_validated_schedules_list(parsing_moderation: ParsingModeration):
    schedules_list = get_parsing_schedules_list(parsing_moderation.parsing)
    assert schedules_list is not None, 'Can not validate parsing with error'

    parsing_moderation.validated_schedules_list = schedules_list.model_dump()
    parsing_moderation.save()

    update_counters_of_parsing(parsing_moderation.parsing)


def has_parsing_been_modified(parsing: Parsing) -> bool:
    non_human_parsing_history = parsing.history.filter(history_user_id__isnull=True) \
        .order_by('-history_date').first()

    if non_human_parsing_history is None:
        # TODO this is not supposed to happen, but it does when human is logged in during parsing
        non_human_parsing_history = parsing.history.filter(history_type='~') \
            .order_by('history_date').first()

    non_human_schedules_list = get_parsing_schedules_list(non_human_parsing_history.instance)
    current_schedule_list = get_parsing_schedules_list(parsing)

    return current_schedule_list != non_human_schedules_list


def update_counters_of_parsing(parsing: Parsing):
    has_been_modified = has_parsing_been_modified(parsing)

    websites_to_update = set()
    for pruning in parsing.prunings.all():
        for scraping in pruning.scrapings.all():
            page = scraping.temp_page
            if has_been_modified:
                page.parsing_validation_counter = -1
            else:
                page.parsing_validation_counter += 1
            page.save()
            websites_to_update.add(page.website)

    for website in websites_to_update:
        if has_been_modified:
            website.parsing_validation_counter = -1
        else:
            website.parsing_validation_counter += 1
        website.save()


def parsing_needs_moderation(parsing: Parsing):
    for pruning in parsing.prunings.all():
        for scraping in pruning.scrapings.all():
            page = scraping.temp_page

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
        print(f'Parsing already exists for pruning {pruning}')
        return

    print(f'parsing {pruning} for website {website}')
    schedules_list, error_detail = parse_with_llm(truncated_html, church_desc_by_id,
                                                  llm_model, prompt_template)

    if parsing:
        parsing.llm_model = llm_model
        parsing.prompt_template_hash = prompt_template_hash
        parsing.error_detail = error_detail
        parsing.save()
    else:
        unlink_website_from_existing_parsing_for_pruning(pruning)

        parsing = Parsing(
            truncated_html=truncated_html,
            truncated_html_hash=truncated_html_hash,
            church_desc_by_id=church_desc_by_id,
            llm_model=llm_model,
            prompt_template_hash=prompt_template_hash,
            error_detail=error_detail,
        )
        parsing.save()

    save_schedule_list(parsing, schedules_list)
    add_necessary_parsing_moderation(parsing, schedules_list)
