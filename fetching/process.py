from fetching.services.oclocher_locations_service import fetch_all_organization_locations
from fetching.services.oclocher_matching_service import match_all_organizations_locations
from fetching.services.oclocher_schedules_service import fetch_all_organization_schedules


def nightly_synchronization():
    # OClocher
    counter = fetch_all_organization_locations()
    print(f"Fetched {counter} OClocher locations.")
    counter = fetch_all_organization_schedules()
    print(f"Fetched {counter} OClocher schedules.")
    match_all_organizations_locations()
