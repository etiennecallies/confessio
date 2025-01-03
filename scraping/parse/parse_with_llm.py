from typing import Optional

from scraping.parse.llm_client import OpenAILLMClient, get_openai_client
from scraping.parse.rrule_utils import are_schedules_list_rrules_valid, \
    is_schedules_list_explainable, filter_unnecessary_schedules
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

Then, "schedules" is a list of dictionaries, each containing the schedule for a church.
Sometimes several schedule dictionaries can be extracted from the same church. If there is no
explicit date in the text, do not return a schedule item dictionary for this event. If there is no
explicit time in the text, do not return a schedule item dictionary for this event neither.

Here is the schedule dictionary format:
{{
    "church_id": Optional[int],  # the id of the respective church, can be null if the
        church information is not explicit in the text. Can be -1 if the church is explicit and is
        not in the provided list. Sometimes, you can guess the church_id when it says
        "à la chapelle" and there is only one church called "chapelle" in the list.
        But if there is no mention, the church_id must be null.
    "date_rule": OneOffRule | RegularRule,  # the recurrence rule for the confession (see below)
    "is_cancellation": bool,  # whether this is a cancellation of a confession, e.g "pas de
        confession en août"
    "start_time_iso8601": Optional[str],  # the start time of the confession in "HH:MM:SS" format,
null if not explicit.
    "end_time_iso8601": Optional[str]  # the end time of the confession in "HH:MM:SS" format,
null if not explicit.
}}

The field "date_rule" is a dictionary describing the date or the dates of confession event. It can
be a one-off date rule or a regular date rule.

Here is the one-off date rule format:
{{
    "year": Optional[int],  # the year as written in the text, let null if not explicit
    "month": int,  # month, only nullable when liturgical_day is specified
    "day": int,  # day of month, only nullable when liturgical_day is specified
    "weekday_iso8601": Optional[int],  # the week day, 1 for Monday to 7, null if not explicit
    "liturgical_day": Optional[LiturgicalDayEnum],  # the liturgical day, null if not explicit
}}

For example, for "Vendredi 30 août", the one-off date rule would be:
{{
    "year": null,
    "month": 8,
    "day": 30,
    "weekday_iso8601": 5,
    "liturgical_day": null
}}, and for "30 août", the one-off date rule would be:
{{
    "year": null,
    "month": 8,
    "day": 30,
    "weekday_iso8601": null,
    "liturgical_day": null
}}.

The accepted LiturgicalDayEnum values are 'ash_wednesday', from 'palms_sunday' to 'easter_sunday',
'ascension' and 'pentecost'.

Here is the regular date rule format:
{{
    "rrule": str,  # the recurrence rule for the confession. For example "DTSTART:20000101
RRULE:FREQ=WEEKLY;BYDAY=WE" for "confession les mercredis de 10h30 à 11h30".
        By default, set 2000 as the year.
    "include_periods": list[PeriodEnum],  # the year periods when the rrule applied. For
        example, if the confession is only during the school holidays, the list would be
        ['school_holidays']. If the expression says "durant l'été", the list would be
        ['july', 'august'].
    "exclude_periods": list[PeriodEnum]  # the year periods excluded. For example, if the
        confession is only during the school terms, the list would be ['school_holidays']. If the
        expression says "sauf pendant le carême", the list would be ['lent'].
}}

The accepted PeriodEnum values are:
- any month from 'january' to 'december'
- 'school_holidays'. If you need 'school_terms', just add 'school_holidays' to the opposite list.
- 'advent' or 'lent' for the liturgical seasons

For example, for "tous les jours sauf en août de 10h à 10h30", the regular date rule would be:
{{
    "rrule": "DTSTART:20000101
RRULE:FREQ=DAILY",
    "include_periods": [],
    "exclude_periods": ["august"]
}}
For "tous les jours sauf en août" without any time, do not return a schedule item dictionary.

Some details:
- EXDATE is not accepted in python rrule, so please do not include it in the rrule, use
    the "exclude_periods" field instead
- rrule must start with "DTSTART:some date", e.g. "DTSTART:20000101"
- if a recurring event description is vague (e.g. "une fois par mois") and is followed by a list of
dates, prefer to return a list of one-off date rules instead of a regular date rule.
- If an expression of en event does not contain a precise date (e.g. "avant Noël"
"avant Pâques", or "une fois par mois") or a precise time (e.g. "dans la matinée",
"dans l'après-midi", "dans la soirée", "après la messe" or no time at all), do not return a schedule
item dictionary for this event. Usually, it means some of the booleans for mass, adoration,
permanence or seasonal events should be set to True.
- A mass lasts 30 minutes, except on Sundays and feast days when it lasts 1 hour. Therefore, if the
confession starts "après la messe", two cases : either the schedule is explicit, e.g
"après la messe de Xh le vendredi" would give a start time of Xh30, or the schedule is not explicit,
e.g. "après la messe" would not give a schedule item dictionary.
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
                      church_desc_by_id: dict[int, str]) -> str:
    church_description = get_church_desc(church_desc_by_id)

    return prompt_template.format(church_description=church_description,
                                  truncated_html=truncated_html)


def build_input_messages(prompt_template: str,
                         truncated_html: str,
                         church_desc_by_id: dict[int, str]) -> list[dict]:
    return [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": build_prompt_text(prompt_template, truncated_html, church_desc_by_id)
                }
            ]
        }
    ]


def get_llm_model():
    # return "gpt-4o-2024-08-06"  # or "gpt-4o-mini"
    # TODO get latest fine-tuned model
    # return 'ft:gpt-4o-2024-08-06:confessio::AHfh95wJ'
    return 'gpt-4o-2024-08-06'


def parse_with_llm(truncated_html: str, church_desc_by_id: dict[int, str],
                   model: str, prompt_template: str,
                   llm_client: Optional[OpenAILLMClient] = None
                   ) -> tuple[Optional[SchedulesList], Optional[str]]:
    if llm_client is None:
        llm_client = OpenAILLMClient(get_openai_client())

    schedules_list, llm_error_detail = llm_client.get_completions(
        model=model,
        messages=build_input_messages(prompt_template, truncated_html, church_desc_by_id),
        temperature=0.0,
    )
    if schedules_list:
        if not are_schedules_list_rrules_valid(schedules_list):
            return None, "Invalid rrules"

        schedules_list.schedules = filter_unnecessary_schedules(schedules_list.schedules)

        if not is_schedules_list_explainable(schedules_list):
            return None, "Not explainable"

    return schedules_list, llm_error_detail


if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    # print(json.dumps(SchedulesList.model_json_schema()))

    truncated_html_ = ("Le sacrement de réconciliation est célébré à l'église Sainte-Marie tous "
                       "les jours de 17h à 18h, et le lundi 30 octobre de 10h à 10h30. Le père "
                       "Jean est disponible pour des confessions sur rendez-vous. Pas de "
                       "confession en août.")

    church_desc_by_id_ = {
        1: "Sainte-Marie, 123 rue de la Paix, 75000 Paris",
        2: "Saint-Joseph, 456 rue de la Liberté, 75000 Paris",
    }

    schedules_list_, llm_error_detail_ = parse_with_llm(truncated_html_, church_desc_by_id_,
                                                        get_llm_model(), get_prompt_template())
    if schedules_list_:
        for schedule in schedules_list_.schedules:
            print(schedule)
        print(schedules_list_.model_dump(exclude={'schedules'}))
    print(llm_error_detail_)

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
