from home.models import Website, WebsiteModeration
from scraping.utils.extract_title import get_page_title


def add_moderation(website: Website, category: WebsiteModeration.Category, home_url):
    try:
        # we need to delete existing moderation first
        existing_category = WebsiteModeration.objects.get(website=website, category=category)
        existing_category.delete()
    except WebsiteModeration.DoesNotExist:
        pass

    website_moderation = WebsiteModeration(
        website=website,
        category=category,
        name=website.name,
        home_url=home_url,
    )
    website_moderation.save()


def update_website_name(website: Website, other_name):
    page_title = get_page_title(website.home_url)

    if page_title:
        # If home_url's title exists we replace website name by it
        website.name = page_title
        moderation_category = WebsiteModeration.Category.NAME_WEBSITE_TITLE
    else:
        # If there is a problem with home_url, new name is concatenation of all names
        previous_sources = website.sources.all()
        all_names = list(map(lambda s: s.name, previous_sources)) + [other_name]
        concatenated_name = ' - '.join(all_names)
        print(f'got new name {concatenated_name}')

        website.name = concatenated_name
        moderation_category = WebsiteModeration.Category.NAME_CONCATENATED

    # We update website
    website.save()

    # We will need to moderate generated website name
    add_moderation(website, moderation_category, website.home_url)


def merge_websites(website: Website, primary_website: Website):
    # We update primary_website name (website title or concatenated names)
    update_website_name(primary_website, website.name)

    # We assign other sources to website
    for source in website.sources.all():
        source.website = primary_website
        source.save()

    # Finally we delete other website
    website.delete()

