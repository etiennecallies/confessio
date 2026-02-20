from uuid import UUID

from front.services.card.church_color_service import get_color_of_nullable_church, \
    get_church_color_by_uuid
from registry.models import Church
from scheduling.public_model import SourcedSchedulesList


def front_get_color_of_nullable_church(church: Church | None,
                                       church_color_by_uuid: dict[UUID, str],
                                       is_church_explicitly_other: bool | None) -> str:
    return get_color_of_nullable_church(church, church_color_by_uuid, is_church_explicitly_other)


def front_get_church_color_by_uuid(sourced_schedules_list: SourcedSchedulesList,
                                   church_by_id: dict[int, Church]) -> dict[UUID, str]:
    return get_church_color_by_uuid(sourced_schedules_list, church_by_id)
