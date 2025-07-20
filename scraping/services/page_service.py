from typing import Optional, Literal

from home.models import Page, Scraping, Pruning, Website
from home.utils.log_utils import info
from scraping.services.parse_pruning_service import unlink_orphan_pruning_for_website
from scraping.services.prune_scraping_service import remove_pruning_if_orphan


############
# DELETION #
############

def delete_page(page: Page):
    if page.scraping is not None:
        delete_scraping(page.scraping)
    page.delete()


def delete_scraping(scraping: Scraping):
    # save prunings to delete
    prunings = list(scraping.prunings.all())

    # save related website
    try:
        website = scraping.page.website
    except Page.DoesNotExist:
        website = None

    scraping.delete()
    check_for_orphan_prunings(prunings, website)


def check_for_orphan_prunings(prunings: list[Pruning], website: Website):
    for pruning in prunings:
        remove_pruning_if_orphan(pruning)
        if website is not None:
            if not pruning.scrapings.filter(page__website=website).exists() \
                    and not pruning.images.filter(website=website).exists():
                unlink_orphan_pruning_for_website(pruning, website)


def clean_scraping_of_pruning(pruning: Pruning):
    for scraping in pruning.scrapings.all():
        try:
            scraping.page
        except Page.DoesNotExist:
            info(f'deleting scraping {scraping} since its page does not exist')
            delete_scraping(scraping)


######################
# QUALITY EVALUATION #
######################

def page_was_validated_at_first(page: Page,
                                resource: Literal['pruning', 'parsing']) -> Optional[bool]:
    for page_version in page.history.all():
        counter = page_version.pruning_validation_counter if resource == 'pruning' else \
            page_version.parsing_validation_counter
        if counter == -1:
            return False

        if counter > 0:
            return True

    return None
