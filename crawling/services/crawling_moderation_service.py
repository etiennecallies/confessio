from crawling.models import CrawlingModeration
from registry.models import Website


def upsert_crawling_moderation(website: Website, category: CrawlingModeration.Category):
    try:
        moderation = CrawlingModeration.objects.get(website=website)
        if moderation.category != category:
            moderation.category = category
            moderation.save()
    except CrawlingModeration.DoesNotExist:
        moderation = CrawlingModeration(
            website=website, category=category,
            diocese=website.get_diocese(),
        )
        moderation.save()
