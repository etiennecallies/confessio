from home.models import Parish, ParishModeration
from scraping.utils.extract_title import get_page_title


def add_moderation(parish: Parish, category: ParishModeration.Category, home_url):
    try:
        # we need to delete existing moderation first
        existing_category = ParishModeration.objects.get(parish=parish, category=category)
        existing_category.delete()
    except ParishModeration.DoesNotExist:
        pass

    parish_moderation = ParishModeration(
        parish=parish,
        category=category,
        name=parish.name,
        home_url=home_url,
    )
    parish_moderation.save()


def update_parish_name(parish: Parish, other_name):
    page_title = get_page_title(parish.home_url)

    if page_title:
        # If home_url's title exists we replace parish name by it
        parish.name = page_title
        moderation_category = ParishModeration.Category.NAME_WEBSITE_TITLE
    else:
        # If there is a problem with home_url, new name is concatenation of all names
        previous_sources = parish.sources.all()
        all_names = list(map(lambda s: s.name, previous_sources)) + [other_name]
        concatenated_name = ' - '.join(all_names)
        print(f'got new name {concatenated_name}')

        parish.name = concatenated_name
        moderation_category = ParishModeration.Category.NAME_CONCATENATED

    # We update parish
    parish.save()

    # We will need to moderate generated parish name
    add_moderation(parish, moderation_category, parish.home_url)


def merge_parishes(parish: Parish, other_parish: Parish):
    # We update parish name (website title or concatenated names)
    update_parish_name(parish, other_parish.name)

    # We assign other sources to parish
    for source in other_parish.sources.all():
        source.parish = parish
        source.save()

    # Finally we delete other parish
    other_parish.delete()

