from datetime import date

from home.models import WebsiteModeration, Website, Church
from sourcing.services.website_url_service import get_alternative_website_url


def remove_not_validated_moderation(website: Website, category: WebsiteModeration.Category):
    try:
        moderation = WebsiteModeration.objects.get(website=website, category=category,
                                                   validated_at__isnull=True)
        moderation.delete()
    except WebsiteModeration.DoesNotExist:
        pass


def add_moderation(website: Website, category: WebsiteModeration.Category,
                   other_website: Website | None = None,
                   other_home_url: str | None = None,
                   conflict_day: date | None = None,
                   conflict_church: Church | None = None):
    try:
        moderation = WebsiteModeration.objects.get(website=website, category=category)
        moderation.home_url = other_home_url[:200] if other_home_url else website.home_url
        moderation.conflict_day = conflict_day
        moderation.conflict_church = conflict_church
        moderation.save()
    except WebsiteModeration.DoesNotExist:
        moderation = WebsiteModeration(
            website=website, category=category,
            other_website=other_website,
            home_url=other_home_url[:200] if other_home_url else website.home_url,
            diocese=website.get_diocese(),
            conflict_day=conflict_day,
            conflict_church=conflict_church,
        )
        moderation.save()


def suggest_alternative_website(website_moderation: WebsiteModeration):
    alternative_website = get_alternative_website_url(website_moderation.website)
    if alternative_website:
        website_moderation.home_url = alternative_website.home_url[:200]
        website_moderation.save()
