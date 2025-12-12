from fetching.models import OClocherOrganization
from fetching.oclocher.fetch_oclocher_api import fetch_organization_locations


def fetch_all_organization_locations():
    oclocher_organizations = OClocherOrganization.objects.all()
    for oclocher_organization in oclocher_organizations:
        # If there are no schedules, we do not bother to fetch locations
        if not oclocher_organization.schedules.exists():
            continue

        fetch_organization_locations(oclocher_organization.organization_id)

    # TODO insert / update OClocherLocation s
