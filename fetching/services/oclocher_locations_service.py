from fetching.models import OClocherOrganization
from fetching.workflows.oclocher.fetch_oclocher_api import fetch_organization_locations


def fetch_oclocher_organization_locations(oclocher_organization: OClocherOrganization) -> bool:
    locations_as_dict = fetch_organization_locations(oclocher_organization.organization_id)

    has_changed = False

    existing_locations = oclocher_organization.locations.all()
    existing_location_by_id = {
        location.location_id: location for location in existing_locations
    }
    for location_as_dict in locations_as_dict:
        location_id = location_as_dict['id']
        name = location_as_dict.get('name')
        address = location_as_dict.get('address')

        if location_id in existing_location_by_id:
            oclocher_location = existing_location_by_id[location_id]
            del existing_location_by_id[location_id]
            if (oclocher_location.name == name
                    and oclocher_location.address == address):
                continue

            oclocher_location.name = name
            oclocher_location.address = address
            oclocher_location.save()
            has_changed = True
            continue

        oclocher_organization.locations.create(
            location_id=location_id,
            name=name,
            address=address,
        )
        has_changed = True

    # Delete locations that are no longer present
    for location in existing_location_by_id.values():
        location.delete()
        has_changed = True

    return has_changed
