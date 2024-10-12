from typing import Optional

from home.utils.date_utils import get_current_year
from scraping.parse.llm_client import OpenAILLMClient, get_openai_client
from scraping.parse.rrule_utils import are_schedules_list_rrules_valid, filter_unnecessary_schedules
from scraping.parse.schedules import SchedulesList


def get_prompt_template():
    return """Please help me extract the schedule of confession from the following French HTML
extract. A confession can be called "confession", "sacrement de réconciliation"
or "soirée de réconciliation, but not "heure de la miséricorde".

The output should be a dictionary with this format:
{{
    "schedules": list[ScheduleItem],  # list of schedule objects, see below
    "possible_by_appointment": bool, # whether the confession is possible by appointment,
        appointment is "rendez-vous" in French
    "is_related_to_mass": bool,  # whether the confession schedule is related to a mass
        schedule
    "is_related_to_adoration": bool,  # whether the confession schedule is related to a
        adoration schedule
    "is_related_to_permanence": bool,  # whether the confession schedule is related to a
        permanence schedule, can be called "permanence" or "accueil" in French.
    "will_be_seasonal_events": bool  # whether the text mentions future confession sessions
        during liturgical seasons, such as Lent or Advent.
}}

Then, "schedules" is of dictionaries, each containing the schedule for a church.
Sometimes several schedule dictionaries can be extracted from the same church.

A schedule dictionary contains recurrence rules for occasional and regular confessions,
as well as the duration of the event.

Here is the schedule dictionary format:
{{
    "church_id": Optional[int],  # the id of the respective church, can be null if the
        church information is not explicit in the text. Can be -1 if the church is explicit and is
        not in the provided list. Sometimes, you can guess the church_id when it says
        "à la chapelle" and there is only one church called "chapelle" in the list.
        But if there is no mention, the church_id must be null.
    "rrule": Optional[str],  # the recurrence rule for the confession. For example
        "DTSTART:{current_year}0101T103000\\nRRULE:FREQ=WEEKLY;BYDAY=WE" for
        "confession les mercredis de 10h30 à 11h30". Can be null if the expression is only
        exclusive.
    "exrule": Optional[str],  # If and only if this is a cancellation definition the expression
        of the "no-confession" rrule. For example "29 septembre de 16h30 à 17h30 Pas de confession"
        "DTSTART:{current_year}0929T163000\\nRRULE:FREQ=DAILY;UNTIL={current_year}0929T173000".
        Null if the expression is not an exclusion.
    "duration_in_minutes": Optional[int],  # the duration of the confession in minutes,
        null if not explicit
    "include_periods": list[PeriodEnum],  # the year periods when the rrule applied. For
        example, if the confession is only during the school holidays, the list would be
        ['school_holidays']. If the expression says "durant l'été", the list would be
        ['july', 'august'].
    "exclude_periods": list[PeriodEnum],  # the year periods excluded. For example, if the
        confession is only during the school terms, the list would be ['school_holidays']. If the
        expression says "sauf pendant le carême", the list would be ['lent'].
}}

The accepted PeriodEnum values are:
- any month from 'january' to 'december'
- 'school_holidays'. If you need 'school_terms', just add 'school_holidays' to the opposite list.
- 'advent' or 'lent' for the liturgical seasons

Some details :
- Consider that we are in year "{current_year}"
- DURATION is not accepted in python rrule, so please do not include it in the rrule, use
    the "duration_in_minutes" field instead
- EXDATE is not accepted in python rrule, so please do not include it in the rrule, use
    the "exclude_periods" field instead
- use FREQ=WEEKLY for weekly schedules, FREQ=DAILY;BYHOUR=... for daily events
- For one-off event, use the keyword UNTIL in the rrule.
    For example, "confession le 8 février de 10h à 11h" would be
    "DTSTART:{current_year}0208T100000\\nRRULE:FREQ=DAILY;UNTIL={current_year}0208T110000"
- If an expression of en event does not contain a precise date (e.g. "avant Noël"
"avant Pâques", or "une fois par mois") or a precise time (e.g. "dans la matinée",
"dans l'après-midi", "dans la soirée" or "après la messe"), do not return a schedule item
dictionary for this event. Usually, it means some of the booleans for mass, adoration, permanence
or seasonal events should be set to True.
- If the church is not explicit in the text, the church_id must be null.

Here is the HTML extract to parse:
{truncated_html}

The church ids and their names and location to consider:
{church_description}"""


def get_church_desc(church_desc_by_id: dict[int, str]):
    return "\n".join(f'{church_id}: {desc}'
                     for church_id, desc in church_desc_by_id.items())


def build_prompt_text(prompt_template: str,
                      truncated_html: str,
                      church_desc_by_id: dict[int, str],
                      current_year: Optional[int]) -> str:
    church_description = get_church_desc(church_desc_by_id)
    current_year = current_year or get_current_year()

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

        schedules_list.schedules = filter_unnecessary_schedules(schedules_list.schedules)

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

    schedules_list_, error_detail_ = parse_with_llm(pruned_html_, church_desc_by_id_,
                                                    get_llm_model(), get_prompt_template())
    if schedules_list_:
        for schedule in schedules_list_.schedules:
            print(schedule)
        print(schedules_list_.model_dump(exclude={'schedules'}))
    print(error_detail_)

    # Expected output:
    # church_id=1
    # rrule='DTSTART:20240101T170000\nRRULE:FREQ=DAILY;BYHOUR=17;BYMINUTE=0'
    # duration_in_minutes=60
    # include_periods=[]
    # exclude_periods=[<PeriodEnum.AUGUST: 'august'>]
    # {'possible_by_appointment': True, 'is_related_to_mass': False,
    # 'is_related_to_adoration': False, 'is_related_to_permanence': False,
    # 'will_be_seasonal_events': False}
    # None
