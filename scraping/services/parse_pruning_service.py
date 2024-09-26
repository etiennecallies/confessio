from typing import Optional

from django.forms import model_to_dict

from home.models import Pruning, Website, Parsing, Schedule, ParsingModeration, Church
from home.utils.hash_utils import hash_string_to_hex
from scraping.parse.parse_with_llm import parse_with_llm, get_llm_model, get_prompt_template
from scraping.parse.schedules import SchedulesList, ScheduleItem

TRUNCATION_LENGTH = 10


def get_truncated_html(pruning: Pruning) -> str:
    lines = pruning.extracted_html.split('<br>\n')

    truncated_lines = []
    last_index = -1
    for index in pruning.pruned_indices:
        if index != last_index + 1:
            truncated_lines.append(f'[{lines[last_index + 1][:TRUNCATION_LENGTH]}...]')
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
    church_index = 1
    for i, desc in enumerate(sorted(church_descs)):
        church_desc_by_id[i + 1] = desc
        church_index += 1

    return church_desc_by_id


def get_id_by_value(church_desc: str, church_desc_by_id: dict[int, str]) -> int:
    for index, desc in church_desc_by_id.items():
        if desc == church_desc:
            return int(index)

    raise ValueError(f'Church description {church_desc} not found in church_desc_by_id')


def get_church_by_id(parsing: Parsing) -> dict[int, Church]:
    church_by_id = {}
    for parish in parsing.website.parishes.all():
        for church in parish.churches.all():
            church_id = get_id_by_value(get_church_desc(church), parsing.church_desc_by_id)
            church_by_id[church_id] = church

    return church_by_id


def get_existing_parsing(website: Website, pruning: Pruning) -> Optional[Parsing]:
    try:
        return Parsing.objects.filter(website=website, pruning=pruning).get()
    except Parsing.DoesNotExist:
        return None


def schedule_item_from_schedule(schedule: Schedule) -> ScheduleItem:
    schedule_dict = model_to_dict(schedule, exclude=['id', 'parsing'])

    return ScheduleItem(**schedule_dict)


def get_parsing_schedules_list(parsing: Parsing) -> Optional[SchedulesList]:
    if parsing.error_detail:
        return None

    return SchedulesList(
        schedules=list(map(schedule_item_from_schedule, parsing.schedules.all())),
        possible_by_appointment=parsing.possible_by_appointment,
        is_related_to_mass=parsing.is_related_to_mass,
        is_related_to_adoration=parsing.is_related_to_adoration,
        is_related_to_permanence=parsing.is_related_to_permanence,
        has_seasonal_events=parsing.has_seasonal_events,
    )


def save_schedule_list(parsing: Parsing, schedules_list: Optional[SchedulesList]):
    if schedules_list is None:
        return

    for schedule_item in schedules_list.schedules:
        schedule = Schedule(
            parsing=parsing,
            **schedule_item.model_dump()
        )
        schedule.save()

    parsing.possible_by_appointment = schedules_list.possible_by_appointment
    parsing.is_related_to_mass = schedules_list.is_related_to_mass
    parsing.is_related_to_adoration = schedules_list.is_related_to_adoration
    parsing.is_related_to_permanence = schedules_list.is_related_to_permanence
    parsing.has_seasonal_events = schedules_list.has_seasonal_events
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
        return

    church_desc_by_id = get_church_desc_by_id(website)

    llm_model = get_llm_model()
    prompt_template = get_prompt_template()
    prompt_template_hash = hash_string_to_hex(prompt_template)

    # check the parsing does not already exist
    parsing = get_existing_parsing(website, pruning)
    if not force_parse and parsing \
            and parsing.church_desc_by_id == church_desc_by_id \
            and parsing.llm_model == llm_model \
            and parsing.prompt_template_hash == prompt_template_hash:
        return

    schedules_list, error_detail = parse_with_llm(truncated_html, church_desc_by_id,
                                                  llm_model, prompt_template)

    if parsing:
        parsing.church_desc_by_id = church_desc_by_id
        parsing.llm_model = llm_model
        parsing.prompt_template_hash = prompt_template_hash
        parsing.error_detail = error_detail
        parsing.save()

        existing_schedules_list = get_parsing_schedules_list(parsing)
        if existing_schedules_list != schedules_list:
            # delete existing schedules
            parsing.schedules.all().delete()
        else:
            return
    else:
        parsing = Parsing(
            website=website,
            pruning=pruning,
            church_desc_by_id=church_desc_by_id,
            llm_model=llm_model,
            prompt_template_hash=prompt_template_hash,
            error_detail=error_detail,
        )
        parsing.save()

    save_schedule_list(parsing, schedules_list)
    add_necessary_parsing_moderation(parsing, schedules_list)
