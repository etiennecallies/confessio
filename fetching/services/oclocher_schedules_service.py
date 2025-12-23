from datetime import datetime

from fetching.models import OClocherOrganization
from fetching.workflows.oclocher.fetch_oclocher_api import fetch_organization_schedules


def extract_datetime(d: dict, key: str) -> datetime | None:
    datetime_str = d.get(key)
    if not datetime_str:
        return None
    return datetime.fromisoformat(datetime_str)


def fetch_oclocher_organization_schedules(oclocher_organization: OClocherOrganization) -> int:
    schedules_as_dict = fetch_organization_schedules(oclocher_organization.organization_id)
    schedules_as_dict_by_location_id = {}
    for schedule in schedules_as_dict:
        schedules_as_dict_by_location_id.setdefault(schedule.get('location'),
                                                    []).append(schedule)

    existing_schedules = oclocher_organization.schedules.all()
    existing_schedule_by_id = {
        schedule.schedule_id: schedule for schedule in existing_schedules
    }

    for location_id, schedules_as_dict_ in schedules_as_dict_by_location_id.items():
        oclocher_location = oclocher_organization.locations.filter(location_id=location_id).first()
        if not oclocher_location:
            raise ValueError(f"Location with id {location_id} not found for organization "
                             f"{oclocher_organization.organization_id} but schedules exist. "
                             f"{schedules_as_dict=}")

        for schedule in schedules_as_dict_:
            schedule_id = schedule['id']
            name = schedule.get('name')
            selection = schedule.get('selection')
            datetime_start = extract_datetime(schedule, 'datetime_start')
            datetime_end = extract_datetime(schedule, 'datetime_finish')
            recurrence_id = schedule.get('recurrence_id')

            if schedule_id in existing_schedule_by_id:
                oclocher_schedule = existing_schedule_by_id[schedule_id]
                del existing_schedule_by_id[schedule_id]

                if (oclocher_schedule.location == oclocher_location
                        and oclocher_schedule.name == name
                        and oclocher_schedule.selection == selection
                        and oclocher_schedule.datetime_start == datetime_start
                        and oclocher_schedule.datetime_end == datetime_end
                        and oclocher_schedule.recurrence_id == recurrence_id):
                    continue

                oclocher_schedule.location = oclocher_location
                oclocher_schedule.name = name
                oclocher_schedule.selection = selection
                oclocher_schedule.datetime_start = datetime_start
                oclocher_schedule.datetime_end = datetime_end
                oclocher_schedule.recurrence_id = recurrence_id
                oclocher_schedule.save()
                continue

            oclocher_organization.schedules.create(
                schedule_id=schedule_id,
                location=oclocher_location,
                name=name,
                selection=selection,
                datetime_start=datetime_start,
                datetime_end=datetime_end,
                recurrence_id=recurrence_id,
            )

    # Delete schedules that are no longer present
    for schedule in existing_schedule_by_id.values():
        schedule.delete()

    return len(schedules_as_dict)


def fetch_all_organization_schedules() -> int:
    oclocher_organizations = OClocherOrganization.objects.all()
    counter = 0
    for oclocher_organization in oclocher_organizations:
        counter += fetch_oclocher_organization_schedules(oclocher_organization)

    return counter
