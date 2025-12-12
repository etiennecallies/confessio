from fetching.services.oclocher_locations_service import fetch_all_organization_locations
from fetching.services.oclocher_matching_service import match_all_organizations_locations
from fetching.services.oclocher_organization_service import \
    remove_oclocher_organization_for_website, add_oclocher_organization_for_website
from fetching.services.oclocher_schedules_service import fetch_all_organization_schedules
from home.models import Website
from scraping.crawl.extract_widgets import BaseWidget, OClocherWidget


def nightly_synchronization():
    # OClocher
    fetch_all_organization_schedules()
    fetch_all_organization_locations()
    match_all_organizations_locations()


def process_extracted_widgets(website: Website, widgets: list[BaseWidget]):
    if not widgets:
        remove_oclocher_organization_for_website(website)
        return

    oclocher_widgets = [w for w in widgets if isinstance(w, OClocherWidget)]
    if oclocher_widgets:
        add_oclocher_organization_for_website(website, oclocher_widgets)
