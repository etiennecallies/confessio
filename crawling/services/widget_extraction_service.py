from crawling.workflows.crawl.extract_widgets import BaseWidget, OClocherWidget
from fetching.public_service import fetching_remove_oclocher_organization_for_website, \
    fetching_add_oclocher_organization_for_website
from registry.models import Website


def process_extracted_widgets(website: Website, widgets: list[BaseWidget]):
    if not widgets:
        fetching_remove_oclocher_organization_for_website(website)
        return

    oclocher_widgets = [w for w in widgets if isinstance(w, OClocherWidget)]
    if oclocher_widgets:
        organization_ids = set([w.organization_id for w in oclocher_widgets])
        fetching_add_oclocher_organization_for_website(website, organization_ids)
