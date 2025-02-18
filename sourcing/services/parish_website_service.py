from home.models import Parish, Website, WebsiteModeration
from sourcing.services.merge_websites_service import add_website_moderation
from sourcing.utils.google_search_api_utils import get_google_search_results


def extract_department_from_messesinfo_community_id(messesinfo_community_id: str) -> str:
    """
    Extract department number from:
    ly/69/la-mulatiere
    """
    splitted_by_slashes = messesinfo_community_id.split('/')
    if len(splitted_by_slashes) != 3:
        return ''

    return splitted_by_slashes[1]


def is_link_ok(link: str) -> bool:
    for domain in ['wikipedia.org', 'messes.info']:
        if domain in link:
            return False

    return True


def save_website_of_parish(parish: Parish) -> Website | None:
    if parish.website:
        return save_website(parish.website)

    # Possibilities to give context to the search:
    # - diocese name or department (we don't have it)
    # - department name from messesinfo_community_id
    # - church city name or churches department name (we don't have it here)

    if not parish.messesinfo_community_id:
        print('no messesinfo_community_id for parish, cannot get website')
        return None

    department = extract_department_from_messesinfo_community_id(parish.messesinfo_community_id)
    if not department:
        print('cannot extract department from messesinfo_community_id')
        return None

    search_query = f"paroisse {parish.name} {department}"
    print(f'searching website for {search_query}')

    google_search_results = get_google_search_results(search_query)
    for result in google_search_results:
        if is_link_ok(result.link):
            print(f'got result {result.title} {result.link}')
            website = save_website(Website(name=result.title, home_url=result.link))
            parish.website = website

            add_website_moderation(website, WebsiteModeration.Category.GOOGLE_SEARCH,
                                   parish.diocese)

            return website

    print(f'no results')
    return None


def save_website(website: Website) -> Website:
    try:
        return Website.objects.get(home_url=website.home_url)
    except Website.DoesNotExist:
        website.save()
        return website
