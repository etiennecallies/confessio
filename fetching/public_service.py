from crawling.workflows.crawl.extract_widgets import BaseWidget, OClocherWidget
from fetching.services.oclocher_organization_service import \
    remove_oclocher_organization_for_website, add_oclocher_organization_for_website
from registry.models import Website


def process_extracted_widgets(website: Website, widgets: list[BaseWidget]):
    if not widgets:
        remove_oclocher_organization_for_website(website)
        return

    oclocher_widgets = [w for w in widgets if isinstance(w, OClocherWidget)]
    if oclocher_widgets:
        add_oclocher_organization_for_website(website, oclocher_widgets)
