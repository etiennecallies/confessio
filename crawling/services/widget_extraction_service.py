from crawling.workflows.crawl.extract_widgets import BaseWidget, OClocherWidget, ContactWidget
from fetching.public_service import fetching_handle_website_widgets
from registry.models import Website
from registry.public_service import registry_set_emails_for_website


def process_oclocher_widgets(website: Website, widgets: list[OClocherWidget]):
    organization_ids = set([w.organization_id for w in widgets])
    fetching_handle_website_widgets(website, organization_ids)


def process_contact_widgets(website: Website, widgets: list[ContactWidget]):
    emails = set([w.email for w in widgets])
    registry_set_emails_for_website(website, emails)


def process_extracted_widgets(website: Website, widgets: list[BaseWidget]):
    process_oclocher_widgets(website, [w for w in widgets if isinstance(w, OClocherWidget)])
    process_contact_widgets(website, [w for w in widgets if isinstance(w, ContactWidget)])
