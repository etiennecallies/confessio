import os
from typing import Optional

from openai import OpenAI, BadRequestError
from pydantic import BaseModel, ValidationError


class ScheduleItem(BaseModel):
    church_id: Optional[int]
    rdates: list[str]
    exdates: list[str]
    rrules: list[str]
    exrules: list[str]
    duration_in_minutes: Optional[int]
    during_school_holidays: Optional[bool]
    possible_by_appointment: bool
    is_related_to_mass: bool
    is_related_to_adoration: bool
    is_related_to_permanence: bool


class SchedulesList(BaseModel):
    schedules: list[ScheduleItem]


def get_openai_client():
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def build_prompt_text(pruned_html: str, location_description_by_church_id: dict[int, str]) -> str:
    church_description = "\n".join(f'{church_id}: {desc}'
                                   for church_id, desc in location_description_by_church_id.items())

    return f"""Please help me extract the schedule of confession from the following French text.
        A confession can be called "confession" or "sacrement de réconciliation"

        The output should be a list of dictionaries, each containing the schedule for a church.
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
                "DTSTART:20240101T103000\\nRRULE:FREQ=WEEKLY;BYDAY=WE" for
                "confession les mercredis de 10h30 à 11h30"
            "exrules": list[str],  # the exception rules for the confession. Set to daily if no
                frequence is specified. For example "pas de confession en aout" would be
                "DTSTART:20240801T000000\\nRRULE:FREQ=DAILY;UNTIL=20240831T000000"
            "duration_in_minutes": Optional[int],  # the duration of the confession in minutes
            "during_school_holidays": Optional[bool],  # whether the schedule concerns only the
                school holidays (true), or explicitely the school term (false) or is not explicit
                about it (null)
            "possible_by_appointment": bool, # whether the confession is possible by appointment
            "is_related_to_mass": bool,  # whether the confession schedule is related to a mass
                schedule
            "is_related_to_adoration": bool,  # whether the confession schedule is related to a
                adoration schedule
            "is_related_to_permanence": bool,  # whether the confession schedule is related to a
                permanence schedule
        }}

        The church ids and their names and location are:
        {church_description}

        Here is the text:
        {pruned_html}"""


def build_input_messages(pruned_html: str,
                         location_description_by_church_id: dict[int, str]) -> list[dict]:
    return [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": build_prompt_text(pruned_html, location_description_by_church_id)
                }
            ]
        }
    ]


def parse_with_llm(pruned_html: str, location_description_by_church_id: dict[int, str]
                   ) -> tuple[Optional[SchedulesList], Optional[str]]:
    client = get_openai_client()
    model = "gpt-4o-2024-08-06"  # or "gpt-4o-mini"

    try:
        response = client.beta.chat.completions.parse(
            model=model,
            messages=build_input_messages(pruned_html, location_description_by_church_id),
            response_format=SchedulesList,
        )
    except BadRequestError as e:
        print(e)
        return None, str(e)
    except ValidationError as e:
        print(e)
        return None, str(e)

    message = response.choices[0].message
    if message.parsed:
        return message.parsed, None
    else:
        return None, message.refusal


if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    # print(json.dumps(SchedulesList.model_json_schema()))

    pruned_html_ = ("Le sacrement de réconciliation est célébré à l'église Sainte-Marie tous les "
                    "jours de 17h à 18h. Le père Jean est disponible pour des confessions sur "
                    "rendez-vous. Pas de confession en août.")

    location_description_by_church_id_ = {
        1: "Sainte-Marie, 123 rue de la Paix, 75000 Paris",
        2: "Saint-Joseph, 456 rue de la Liberté, 75000 Paris",
    }

    # Expected output:
    # church_id = 1
    # rdates = []
    # exdates = []
    # rrules = ['DTSTART:20240101T170000\\nRRULE:FREQ=DAILY']
    # exrules = ['DTSTART:20240801T000000\\nRRULE:FREQ=DAILY;UNTIL=20240831T000000']
    # duration_in_minutes = 60
    # during_school_holidays = None
    # possible_by_appointment = True
    # is_related_to_mass = False
    # is_related_to_adoration = False
    # is_related_to_permanence = False

    schedules_list, error_detail = parse_with_llm(pruned_html_, location_description_by_church_id_)
    if schedules_list:
        for schedule in schedules_list.schedules:
            print(schedule)
    print(error_detail)
