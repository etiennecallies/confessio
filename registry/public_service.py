from registry.models import WebsiteModeration, Website
from registry.services.church_location_service import find_church_geo_outliers
from registry.services.website_contact_service import set_emails_for_website
from registry.services.website_moderation_service import remove_not_validated_moderation, \
    add_website_moderation, suggest_alternative_website


def registry_remove_not_validated_moderation(website: Website,
                                             category: WebsiteModeration.Category):
    return remove_not_validated_moderation(website, category)


def registry_add_website_moderation(website: Website, category: WebsiteModeration.Category,
                                    other_website: Website | None = None,
                                    other_home_url: str | None = None):
    return add_website_moderation(website, category, other_website, other_home_url)


def registry_suggest_alternative_website(website_moderation: WebsiteModeration):
    return suggest_alternative_website(website_moderation)


def registry_set_emails_for_website(website: Website, emails: set[str]):
    set_emails_for_website(website, emails)


def registry_find_church_geo_outliers() -> int:
    return find_church_geo_outliers()
