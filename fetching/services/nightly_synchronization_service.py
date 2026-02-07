from fetching.models import OClocherOrganization
from fetching.services.oclocher_locations_service import fetch_oclocher_organization_locations
from fetching.services.oclocher_schedules_service import fetch_oclocher_organization_schedules
from scheduling.public_service import scheduling_init_scheduling


def nightly_synchronization():
    # OClocher
    oclocher_organizations = OClocherOrganization.objects.all()

    counter = 0
    for oclocher_organization in oclocher_organizations:
        has_changed1 = fetch_oclocher_organization_locations(oclocher_organization)
        has_changed2 = fetch_oclocher_organization_schedules(oclocher_organization)
        if has_changed1 or has_changed2:
            counter += 1
            scheduling_init_scheduling(oclocher_organization.website)

    print(f"Got {counter} OClocher organization with change in locations or schedules.")
