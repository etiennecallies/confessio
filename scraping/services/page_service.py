from typing import Optional, Literal

from home.models import Page, Scraping
from scraping.services.prune_scraping_service import remove_pruning_if_orphan


############
# DELETION #
############

def delete_page(page: Page):
    if page.scraping is not None:
        delete_scraping(page.scraping)
    page.delete()


def delete_scraping(scraping: Scraping):
    prunings = scraping.prunings.all()
    scraping.delete()
    for pruning in prunings:
        remove_pruning_if_orphan(pruning)


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
