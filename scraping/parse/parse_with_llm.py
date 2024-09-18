from datetime import datetime
from typing import Optional

from scraping.parse.llm_client import OpenAILLMClient, get_openai_client
from scraping.parse.schedules import SchedulesList
from scraping.parse.test_rrule import are_schedules_list_rrules_valid


def get_prompt_template():
    return """Please help me extract the schedule of confession from the following French text.
        A confession can be called "confession" or "sacrement de réconciliation"

        The output should be a dictionary with this format:
        {{
            "schedules": list[ScheduleItem],  # list of schedule objects, see below
            "possible_by_appointment": bool, # whether the confession is possible by appointment
            "is_related_to_mass": bool,  # whether the confession schedule is related to a mass
                schedule
            "is_related_to_adoration": bool,  # whether the confession schedule is related to a
                adoration schedule
            "is_related_to_permanence": bool  # whether the confession schedule is related to a
                permanence schedule
        }}

        Then, "schedules" is of dictionaries, each containing the schedule for a church.
        Sometimes several schedule dictionaries can be extracted from the same church.

        A schedule dictionary contains recurrence rules for occasional and regular confessions,
        as well as the duration of the event.

        Here is the schedule dictionary format:
        {{
            "church_id": Optional[int],  # the id of the respective church, can be null if the
                church information is not explicit in the text
            "rdates": list[str],  # the start dates of the confession. Can be empty.
            "exdates": list[str],  # the exception start dates for the confession.
                Set to midnight if no hour specified.
            "rrules": list[str],  # the recurrence rules for the confession. For example
                "DTSTART:{current_year}0101T103000\\nRRULE:FREQ=WEEKLY;BYDAY=WE" for
                "confession les mercredis de 10h30 à 11h30"
            "exrules": list[str],  # the exception rules for the confession. Set to daily if no
                frequence is specified. For example "pas de confession en aout" would be
                "DTSTART:{current_year}0801T000000\\nRRULE:FREQ=DAILY;UNTIL={current_year}0831T000000"
            "duration_in_minutes": Optional[int],  # the duration of the confession in minutes,
                null if not explicit
            "during_school_holidays": Optional[bool]  # whether the schedule concerns only the
                school holidays (true), or explicitely the school term (false) or is not explicit
                about it (null)
        }}

        Some details :
        - Consider that we are in year "{current_year}"
        - When it says "pas de confession pendant l'été", it means "no confession during july and
            august"
        - DURATION is not accepted in python rrule, so please do not include it in the rrule, use
            the "duration_in_minutes" field instead


        The church ids and their names and location are:
        {church_description}

        Here is the text:
        {truncated_html}"""


def build_prompt_text(prompt_template: str,
                      truncated_html: str,
                      church_desc_by_id: dict[int, str],
                      current_year: Optional[int]) -> str:
    church_description = "\n".join(f'{church_id}: {desc}'
                                   for church_id, desc in church_desc_by_id.items())
    current_year = current_year or datetime.now().year

    return prompt_template.format(current_year=current_year,
                                  church_description=church_description,
                                  truncated_html=truncated_html)


def build_input_messages(prompt_template: str,
                         truncated_html: str,
                         church_desc_by_id: dict[int, str],
                         current_year: Optional[int]) -> list[dict]:
    return [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": build_prompt_text(prompt_template, truncated_html, church_desc_by_id,
                                              current_year)
                }
            ]
        }
    ]


def get_llm_model():
    return "gpt-4o-2024-08-06"  # or "gpt-4o-mini"


def parse_with_llm(truncated_html: str, church_desc_by_id: dict[int, str],
                   model: str, prompt_template: str,
                   llm_client: Optional[OpenAILLMClient] = None,
                   current_year: Optional[int] = None
                   ) -> tuple[Optional[SchedulesList], Optional[str]]:
    if llm_client is None:
        llm_client = OpenAILLMClient(get_openai_client())

    schedules_list, error_detail = llm_client.get_completions(
        model=model,
        messages=build_input_messages(prompt_template, truncated_html, church_desc_by_id,
                                      current_year),
        temperature=0.0,
    )
    if schedules_list:
        if not are_schedules_list_rrules_valid(schedules_list):
            return None, "Invalid rrules"

    return schedules_list, error_detail


if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    # print(json.dumps(SchedulesList.model_json_schema()))

    pruned_html_ = ("Le sacrement de réconciliation est célébré à l'église Sainte-Marie tous les "
                    "jours de 17h à 18h. Le père Jean est disponible pour des confessions sur "
                    "rendez-vous. Pas de confession en août.")

    church_desc_by_id_ = {
        1: "Sainte-Marie, 123 rue de la Paix, 75000 Paris",
        2: "Saint-Joseph, 456 rue de la Liberté, 75000 Paris",
    }

    # Expected output:
    # church_id = 1
    # rdates = ''
    # exdates = ''
    # rrules = 'DTSTART:20240101T170000\nRRULE:FREQ=DAILY'
    # exrules = 'DTSTART:20240801T000000\nRRULE:FREQ=DAILY;UNTIL=20240831T000000'
    # duration_in_minutes = 60
    # during_school_holidays = None
    # {'possible_by_appointment': True, 'is_related_to_mass': False,
    # 'is_related_to_adoration': False, 'is_related_to_permanence': False}

    schedules_list_, error_detail_ = parse_with_llm(pruned_html_, church_desc_by_id_,
                                                    get_llm_model(), get_prompt_template())
    if schedules_list_:
        for schedule in schedules_list_.schedules:
            print(schedule)
        print(schedules_list_.model_dump(exclude={'schedules'}))
    print(error_detail_)
