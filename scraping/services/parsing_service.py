from home.models import Parsing, Church
from home.utils.log_utils import info
from scraping.parse.schedules import SchedulesList, SCHEDULES_LIST_VERSION
from scraping.parse.v1_0_to_v1_1 import from_v1_0_to_v1_1


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


def get_dict_and_version(parsing: Parsing) -> tuple[dict, str]:
    if parsing.human_json:
        return parsing.human_json, parsing.human_json_version

    return parsing.llm_json, parsing.llm_json_version


def get_parsing_schedules_list(parsing: Parsing) -> SchedulesList | None:
    schedules_list_as_dict, version = get_dict_and_version(parsing)
    if schedules_list_as_dict is None:
        return None

    if version == 'v1.0':
        return from_v1_0_to_v1_1(schedules_list_as_dict)
    if version == SCHEDULES_LIST_VERSION:
        return SchedulesList(**schedules_list_as_dict)

    raise ValueError(f'Unknown parsing version {version}')
