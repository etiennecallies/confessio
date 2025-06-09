from home.models import Website
from sourcing.services.parish_website_service import get_new_website_for_parish


def get_alternative_website_url(website: Website) -> Website | None:
    if len(website.parishes.all()) == 1:
        return get_new_website_for_parish(website.parishes.first())

    return None
