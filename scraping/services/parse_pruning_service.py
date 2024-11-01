from typing import Optional

from django.forms import model_to_dict
from pydantic import ValidationError

from home.models import Pruning, Website, Parsing, Schedule, ParsingModeration, Church, \
    OneOffSchedule, RegularSchedule
from home.utils.hash_utils import hash_string_to_hex
from scraping.parse.parse_with_llm import parse_with_llm, get_llm_model, get_prompt_template
from scraping.parse.schedules import SchedulesList, ScheduleItem
from scraping.refine.refine_content import remove_link_from_html

TRUNCATION_LENGTH = 10
MAX_LENGTH_FOR_PARSING = 3000


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


def get_church_desc(church: Church) -> str:
    return f'{church.name} {church.city}'


def get_church_desc_by_id(website: Website) -> dict[int, str]:
    church_descs = []
    for parish in website.parishes.all():
        for church in parish.churches.all():
            church_descs.append(get_church_desc(church))

    church_desc_by_id = {}
    for i, desc in enumerate(sorted(church_descs)):
        church_desc_by_id[i] = desc

    return church_desc_by_id


def get_id_by_value(church_desc: str, church_desc_by_id: dict[int, str]) -> int:
    for index, desc in church_desc_by_id.items():
        if desc == church_desc:
            return int(index)

    raise ValueError(f'Church description {church_desc} not found in church_desc_by_id')


def get_church_by_id(parsing: Parsing, website: Website) -> dict[int, Church]:
    church_by_id = {}
    for parish in website.parishes.all():
        for church in parish.churches.all():
            church_id = get_id_by_value(get_church_desc(church), parsing.church_desc_by_id)
            church_by_id[church_id] = church

    return church_by_id


def get_existing_parsing(truncated_html: str,
                         church_desc_by_id: dict[int, str]) -> Optional[Parsing]:
    try:
        return Parsing.objects.filter(truncated_html=truncated_html,
                                      church_desc_by_id=church_desc_by_id).get()
    except Parsing.DoesNotExist:
        return None


def schedule_item_from_schedule(schedule: Schedule) -> ScheduleItem:
    base_fields = ['church_id', 'is_exception_rule', 'duration_in_minutes']
    exclude_fields = ['id', 'schedule']

    schedule_dict = model_to_dict(schedule, fields=base_fields)
    schedule_dict['rule'] = model_to_dict(schedule, exclude=base_fields + exclude_fields)

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

    base_fields = {'church_id', 'is_exception_rule', 'duration_in_minutes'}
    for schedule_item in schedules_list.schedules:
        if schedule_item.is_one_off_rule():
            schedule = OneOffSchedule(
                parsing=parsing,
                **schedule_item.model_dump(include=base_fields),
                **schedule_item.date_rule.model_dump()
            )
        elif schedule_item.is_regular_rule():
            schedule = RegularSchedule(
                parsing=parsing,
                **schedule_item.model_dump(include=base_fields),
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


def add_necessary_parsing_moderation(parsing: Parsing, schedules_list: Optional[SchedulesList]):
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


def parse_pruning_for_website(pruning: Pruning, website: Website, force_parse: bool = False):
    truncated_html = get_truncated_html(pruning)
    if not truncated_html:
        # no parsing on empty content
        return

    if len(truncated_html) > MAX_LENGTH_FOR_PARSING:
        print(f'No parsing above {MAX_LENGTH_FOR_PARSING}, got {len(truncated_html)}')
        return

    truncated_html_hash = hash_string_to_hex(truncated_html)

    church_desc_by_id = get_church_desc_by_id(website)

    llm_model = get_llm_model()
    prompt_template = get_prompt_template()
    prompt_template_hash = hash_string_to_hex(prompt_template)

    # check the parsing does not already exist
    parsing = get_existing_parsing(truncated_html, church_desc_by_id)
    if not force_parse and parsing \
            and parsing.llm_model == llm_model \
            and parsing.prompt_template_hash == prompt_template_hash:
        return

    schedules_list, error_detail = parse_with_llm(truncated_html, church_desc_by_id,
                                                  llm_model, prompt_template)

    if parsing:
        parsing.llm_model = llm_model
        parsing.prompt_template_hash = prompt_template_hash
        parsing.error_detail = error_detail
        parsing.save()
    else:
        parsing = Parsing(
            truncated_html=truncated_html,
            truncated_html_hash=truncated_html_hash,
            church_desc_by_id=church_desc_by_id,
            llm_model=llm_model,
            prompt_template_hash=prompt_template_hash,
            error_detail=error_detail,
        )
        parsing.save()

    parsing.websites.add(website)
    parsing.prunings.add(pruning)

    save_schedule_list(parsing, schedules_list)
    add_necessary_parsing_moderation(parsing, schedules_list)
