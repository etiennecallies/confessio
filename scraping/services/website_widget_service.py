from home.models import Website, WebsiteModeration
from home.utils.log_utils import info
from scraping.crawl.download_and_search_urls import CrawlingResult
from scraping.crawl.extract_widgets import OClocherWidget
from scraping.services.website_moderation_service import add_moderation


def process_oclocher_widgets(website: Website, oclocher_widgets: list[OClocherWidget]):
    organization_ids = set([w.organization_id for w in oclocher_widgets])
    if len(organization_ids) > 1:
        info(f"Multiple oclocher organization IDs found for website {website}: "
             f"{organization_ids}. Not updating.")
        add_moderation(website, WebsiteModeration.Category.OCLOCHER_CONFLICT)
        return

    organization_id = organization_ids.pop()
    if website.oclocher_organization_id != organization_id:
        info(f"Updating oclocher organization ID for website {website} "
             f"from {website.oclocher_organization_id} to {organization_id}")
        website.oclocher_organization_id = organization_id
        website.save()
    else:
        info(f"Oclocher organization ID for website {website} "
             f"remains unchanged: {organization_id}")


def process_extracted_widgets(website: Website, crawling_result: CrawlingResult):
    if not crawling_result.widgets_by_url:
        if website.oclocher_organization_id:
            info(f"Removing oclocher organization ID for website {website} "
                 f"due to no widgets found")
            website.oclocher_organization_id = None
            website.save()
        return

    process_oclocher_widgets(website, [w for (_, widgets) in crawling_result.widgets_by_url.items()
                                       for w in widgets
                                       if isinstance(w, OClocherWidget)])
