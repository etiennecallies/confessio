from home.models import Page, Scraping, Pruning
from home.utils.log_utils import info
from scraping.services.prune_scraping_service import remove_pruning_moderation_if_orphan


############
# DELETION #
############

def delete_page(page: Page):
    info(f'deleting page with url {page.url} of website {page.website.uuid}')
    if page.has_been_scraped():
        delete_scraping(page.scraping)
    page.delete()


def delete_scraping(scraping: Scraping):
    info(f'deleting scraping {scraping} of website {scraping.page.website.uuid}')
    # save prunings to delete
    prunings = list(scraping.prunings.all())

    scraping.delete()
    check_for_orphan_prunings(prunings)


def check_for_orphan_prunings(prunings: list[Pruning]):
    for pruning in prunings:
        remove_pruning_moderation_if_orphan(pruning)
