from home.models import Parish, Website, WebsiteModeration
from scraping.utils.string_search import normalize_content, get_words
from sourcing.services.merge_websites_service import add_website_moderation
from sourcing.services.website_name_service import clean_website_name
from sourcing.utils.extract_title import get_page_title
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
    for domain in [
        'messes.info',
        'theodia.org',
        '4paroisses.fr',
        '4clochers.fr',
        'horairesmesses.com',
        'lejourduseigneur.com',

        'wikipedia.org',
        'fondation-patrimoine.org',
        'pagesjaunes.fr',
        'boulevarddesdecouvertes.com',
        'infolocale.fr',
        'actu.fr',
        'lavieb-aile.com',
        'tourismepaysroimorvan.com',
        'rochefortenterre-tourisme.bzh',
        'ouest-france.fr',
        'letelegramme.fr',
        'infobretagne.com',

        'facebook.com',
        'instagram.com',
    ]:
        if domain in link:
            return False

    return True


def is_title_ok(title: str) -> bool:
    normalized_content = normalize_content(title)
    words_set = set(get_words(normalized_content))

    for keyword in [
        'mairie',
        'tourisme',
    ]:
        if keyword in words_set:
            return False

    return True


def get_new_website_for_parish(parish: Parish) -> Website | None:
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
        if is_link_ok(result.link) and is_title_ok(result.title):
            print(f'got result {result.title} {result.link}')
            # We can not take result.title since it's truncated by google
            website_title = get_page_title(result.link)
            if not website_title:
                print(f'got no title for {result.link} (Google said "{result.title}")')
                continue

            return Website(name=website_title, home_url=result.link)

    return None


def save_website_of_parish(parish: Parish) -> Website | None:
    if parish.website:
        return save_website(parish.website)

    new_website = get_new_website_for_parish(parish)
    if new_website:
        website = save_website(new_website)
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
        clean_website_name(website)
        return website
