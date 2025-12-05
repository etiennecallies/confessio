from fetching.services.oclocher_locations_service import fetch_all_organization_locations
from fetching.services.oclocher_matching_service import match_all_organizations_locations
from fetching.services.oclocher_schedules_service import fetch_all_organization_schedules


def nightly_synchronization():
    # OClocher
    fetch_all_organization_schedules()
    fetch_all_organization_locations()
    match_all_organizations_locations()
