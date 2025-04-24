from home.models import Parsing, Website, Church
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


def get_church_by_id(parsing: Parsing, website: Website) -> dict[int, Church]:
    church_by_id = {}
    for parish in website.parishes.all():
        for church in parish.churches.all():
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


def get_parsing_schedules_list(parsing: Parsing) -> SchedulesList | None:
    schedules_list_as_dict = parsing.human_json or parsing.llm_json
    if schedules_list_as_dict is None:
        return None

    return SchedulesList(**schedules_list_as_dict)
