from registry.models import WebsiteModeration, Website
from registry.services.merge_websites_service import merge_websites
from registry.services.website_contact_service import set_emails_for_website
from registry.services.website_moderation_service import remove_not_validated_moderation, \
    add_website_moderation


def registry_remove_not_validated_moderation(website: Website,
                                             category: WebsiteModeration.Category):
    return remove_not_validated_moderation(website, category)


def registry_add_website_moderation(website: Website, category: WebsiteModeration.Category,
                                    other_website: Website | None = None,
                                    other_home_url: str | None = None):
    return add_website_moderation(website, category, other_website, other_home_url)


def registry_merge_websites(website: Website, primary_website: Website):
    return merge_websites(website, primary_website)


def registry_set_emails_for_website(website: Website, emails: set[str]):
    set_emails_for_website(website, emails)
