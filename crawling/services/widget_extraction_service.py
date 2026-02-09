from crawling.workflows.crawl.extract_widgets import BaseWidget, OClocherWidget, ContactWidget
from fetching.public_service import fetching_remove_oclocher_organization_for_website, \
    fetching_add_oclocher_organization_for_website
from registry.models import Website


def process_oclocher_widgets(website: Website, widgets: list[OClocherWidget]):
    if not widgets:
        fetching_remove_oclocher_organization_for_website(website)
        return

    organization_ids = set([w.organization_id for w in widgets])
    fetching_add_oclocher_organization_for_website(website, organization_ids)


def process_contact_widgets(website: Website, widgets: list[ContactWidget]):
    # TODO
    pass


def process_extracted_widgets(website: Website, widgets: list[BaseWidget]):
    process_oclocher_widgets(website, [w for w in widgets if isinstance(w, OClocherWidget)])
    process_contact_widgets(website, [w for w in widgets if isinstance(w, ContactWidget)])
