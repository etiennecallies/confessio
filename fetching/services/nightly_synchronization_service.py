from fetching.models import OClocherOrganization
from fetching.services.oclocher_locations_service import fetch_oclocher_organization_locations
from fetching.services.oclocher_organizations_service import fetch_oclocher_organizations
from fetching.services.oclocher_schedules_service import fetch_oclocher_organization_schedules
from scheduling.public_service import scheduling_init_scheduling


def nightly_synchronization():
    # OClocher
    fetched, added, same, edited, deleted = fetch_oclocher_organizations()
    print(f"Fetched {fetched} OClocher organizations, added {added}, same {same}, edited {edited},"
          f" deleted {deleted}.")
    oclocher_organizations = OClocherOrganization.objects.filter(website__isnull=False).all()
    print(f"Got {len(oclocher_organizations)} OClocher organizations with website.")

    counter = 0
    for oclocher_organization in oclocher_organizations:
        has_changed1 = fetch_oclocher_organization_locations(oclocher_organization)
        has_changed2 = fetch_oclocher_organization_schedules(oclocher_organization)
        if has_changed1 or has_changed2:
            counter += 1
            scheduling_init_scheduling(oclocher_organization.website)

    print(f"Got {counter} OClocher organization with change in locations or schedules.")
