from django.db.models.functions import Now

from crawling.models import CrawlingModeration
from crawling.workflows.crawl.download_and_search_urls import CrawlingResult
from registry.models import Website


def upsert_crawling_moderation(website: Website, category: CrawlingModeration.Category,
                               moderation_validated: bool) -> CrawlingModeration:
    try:
        moderation = CrawlingModeration.objects.get(website=website)
        if moderation.category != category:
            moderation.category = category
            moderation.validated_at = Now() if moderation_validated else None
            moderation.validated_by = None
            moderation.save()
    except CrawlingModeration.DoesNotExist:
        moderation = CrawlingModeration(
            website=website, category=category,
            diocese=website.get_diocese(),
            validated_at=Now() if moderation_validated else None,
        )
        moderation.save()

    return moderation


def get_crawling_moderation_category(website: Website,
                                     crawling_result: CrawlingResult
                                     ) -> tuple[CrawlingModeration.Category, bool]:
    if crawling_result.confession_pages and website.scrapings.exists():
        return CrawlingModeration.Category.OK, True
    elif crawling_result.visited_links_count > 0:
        return CrawlingModeration.Category.NO_PAGE, False
    else:
        return CrawlingModeration.Category.NO_RESPONSE, False
