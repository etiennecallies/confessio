from datetime import date

from registry.models import WebsiteModeration, Website, Church
from registry.services.website_moderation_service import remove_not_validated_moderation, \
    add_website_moderation, suggest_alternative_website


def registry_remove_not_validated_moderation(website: Website,
                                             category: WebsiteModeration.Category):
    return remove_not_validated_moderation(website, category)


def registry_add_website_moderation(website: Website, category: WebsiteModeration.Category,
                                    other_website: Website | None = None,
                                    other_home_url: str | None = None,
                                    conflict_day: date | None = None,
                                    conflict_church: Church | None = None):
    return add_website_moderation(website, category, other_website, other_home_url, conflict_day,
                                  conflict_church)


def registry_suggest_alternative_website(website_moderation: WebsiteModeration):
    return suggest_alternative_website(website_moderation)
