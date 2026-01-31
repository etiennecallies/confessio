from datetime import date

from registry.models import WebsiteModeration, Website, Church
from registry.services.website_url_service import get_alternative_website_url


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
    home_url = other_home_url[:200] if other_home_url else website.home_url
    try:
        moderation = WebsiteModeration.objects.get(website=website, category=category)
        if moderation.home_url != home_url or \
                moderation.other_website != other_website or \
                moderation.conflict_day != conflict_day or \
                moderation.conflict_church != conflict_church:
            moderation.home_url = home_url
            moderation.other_website = other_website
            moderation.conflict_day = conflict_day
            moderation.conflict_church = conflict_church
            moderation.save()
    except WebsiteModeration.DoesNotExist:
        moderation = WebsiteModeration(
            website=website, category=category,
            other_website=other_website,
            home_url=home_url,
            diocese=website.get_diocese(),
            conflict_day=conflict_day,
            conflict_church=conflict_church,
        )
        moderation.save()


def suggest_alternative_website(website_moderation: WebsiteModeration):
    alternative_website = get_alternative_website_url(website_moderation.website)
    if alternative_website:
        alternative_url = alternative_website.home_url[:200]
        if website_moderation.home_url != alternative_url:
            website_moderation.home_url = alternative_url
            website_moderation.save()
