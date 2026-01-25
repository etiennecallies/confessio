from scheduling.models.parsing_models import Parsing
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

def get_parsing_church_desc_by_id(parsing: Parsing) -> dict[int, str]:
    return {int(church_id): church_desc
            for church_id, church_desc in parsing.church_desc_by_id.items()}


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


def get_schedules_list_from_dict(schedules_list_as_dict: dict, version: str
                                 ) -> SchedulesList | None:
    if version == 'v1.0':
        return from_v1_0_to_v1_1(schedules_list_as_dict)
    if version == SCHEDULES_LIST_VERSION:
        return SchedulesList(**schedules_list_as_dict)

    raise ValueError(f'Unknown parsing version {version}')


def get_parsing_schedules_list(parsing: Parsing) -> SchedulesList | None:
    schedules_list_as_dict, version = get_dict_and_version(parsing)
    if schedules_list_as_dict is None:
        return None

    return get_schedules_list_from_dict(schedules_list_as_dict, version)
