from home.models import Parsing, Church
from home.utils.log_utils import info
from scraping.parse.schedules import SchedulesList


######################
# CHECK IF NOT EMPTY #
######################

def has_schedules(parsing: Parsing) -> bool:
    schedules_list = get_parsing_schedules_list(parsing)
    if not schedules_list:
        return False

    return (schedules_list.schedules
            or schedules_list.is_related_to_permanence
            or schedules_list.is_related_to_adoration
            or schedules_list.is_related_to_mass
            or schedules_list.possible_by_appointment
            or schedules_list.will_be_seasonal_events)


###############
# CHURCH DESC #
###############

def get_id_by_value(church_desc: str, church_desc_by_id: dict[int, str]) -> int | None:
    for index, desc in church_desc_by_id.items():
        if desc == church_desc:
            return int(index)

    return None


def get_church_by_id(parsing: Parsing, website_churches: list[Church]) -> dict[int, Church]:
    church_by_id = {}
    for church in website_churches:
        church_id = get_id_by_value(church.get_desc(), parsing.church_desc_by_id)
        if church_id is not None:
            church_by_id[church_id] = church
        else:
            info(f'Church {church} not found in church_desc_by_id for parsing {parsing}')

    return church_by_id


########################
# PARSING MANIPULATION #
########################

BASE_FIELDS = {'church_id', 'is_cancellation', 'start_time_iso8601', 'end_time_iso8601'}


def get_existing_parsing(truncated_html_hash: str,
                         church_desc_by_id: dict[int, str]) -> Parsing | None:
    try:
        return Parsing.objects.filter(truncated_html_hash=truncated_html_hash,
                                      church_desc_by_id=church_desc_by_id).get()
    except Parsing.DoesNotExist:
        return None


def from_v1_0_to_v1_1(schedules_list_json: dict):
    # if period == PeriodEnum.JANUARY:
    #     return [(date(year, 1, 1), date(year, 1, 31))]
    # if period == PeriodEnum.FEBRUARY:
    #     # handle leap years
    #     if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
    #         return [(date(year, 2, 1), date(year, 2, 29))]
    #     else:
    #         return [(date(year, 2, 1), date(year, 2, 28))]
    # if period == PeriodEnum.MARCH:
    #     return [(date(year, 3, 1), date(year, 3, 31))]
    # if period == PeriodEnum.APRIL:
    #     return [(date(year, 4, 1), date(year, 4, 30))]
    # if period == PeriodEnum.MAY:
    #     return [(date(year, 5, 1), date(year, 5, 31))]
    # if period == PeriodEnum.JUNE:
    #     return [(date(year, 6, 1), date(year, 6, 30))]
    # if period == PeriodEnum.JULY:
    #     return [(date(year, 7, 1), date(year, 7, 31))]
    # if period == PeriodEnum.AUGUST:
    #     return [(date(year, 8, 1), date(year, 8, 31))]
    # if period == PeriodEnum.SEPTEMBER:
    #     return [(date(year, 9, 1), date(year, 9, 30))]
    # if period == PeriodEnum.OCTOBER:
    #     return [(date(year, 10, 1), date(year, 10, 31))]
    # if period == PeriodEnum.NOVEMBER:
    #     return [(date(year, 11, 1), date(year, 11, 30))]
    # if period == PeriodEnum.DECEMBER:
    #     return [(date(year, 12, 1), date(year, 12, 31))]
    pass


def get_parsing_schedules_list(parsing: Parsing) -> SchedulesList | None:
    schedules_list_as_dict = parsing.human_json or parsing.llm_json
    if schedules_list_as_dict is None:
        return None

    return SchedulesList(**schedules_list_as_dict)
