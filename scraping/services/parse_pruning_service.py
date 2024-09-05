from home.models import Pruning, Website, Parsing, Schedule
from home.utils.hash_utils import hash_string_to_hex
from scraping.parse.parse_with_llm import parse_with_llm, get_llm_model, get_prompt_template

TRUNCATION_LENGTH = 10


def get_truncated_html(pruning: Pruning) -> str:
    lines = pruning.extracted_html.split('<br>\n')

    truncated_html = ''
    last_index = -1
    for index in pruning.pruned_indices:
        if index != last_index + 1:
            truncated_html += f'[{lines[last_index + 1][:TRUNCATION_LENGTH]}...]'
        truncated_html += lines[index]
        last_index = index

    return truncated_html


def get_church_desc_by_id(website: Website):
    church_descs = []
    for parish in website.parishes.all():
        for church in parish.churches.all():
            church_descs.append(f'{church.name} {church.city}')

    church_desc_by_id = {}
    church_index = 1
    for i, desc in enumerate(sorted(church_descs)):
        church_desc_by_id[i + 1] = desc
        church_index += 1

    return church_desc_by_id


def parse_pruning_for_website(pruning: Pruning, website: Website):
    truncated_html = get_truncated_html(pruning)
    church_desc_by_id = get_church_desc_by_id(website)

    # check the parsing does not already exist
    if Parsing.objects.filter(pruning=pruning,
                              church_desc_by_id=church_desc_by_id).exists():
        return

    llm_model = get_llm_model()
    prompt_template = get_prompt_template()
    schedules_list, error_detail = parse_with_llm(truncated_html, church_desc_by_id,
                                                  llm_model, prompt_template)

    parsing = Parsing(
        pruning=pruning,
        church_desc_by_id=church_desc_by_id,
        llm_model=llm_model,
        prompt_template_hash=hash_string_to_hex(prompt_template),
        error_detail=error_detail,
    )
    parsing.save()

    if schedules_list:
        for schedule_item in schedules_list.schedules:
            schedule = Schedule(
                parsing=parsing,
                **schedule_item.model_dump()
            )
            schedule.save()
