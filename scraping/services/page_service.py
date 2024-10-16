from typing import Optional

from home.models import Page, Pruning, Scraping, PruningModeration, ParsingModeration


############
# DELETION #
############

def delete_page(page: Page):
    pruning = page.get_latest_pruning()
    page.delete()
    remove_pruning_if_orphan(pruning)


def delete_scraping(scraping: Scraping):
    pruning = scraping.pruning
    scraping.delete()
    remove_pruning_if_orphan(pruning)


def remove_pruning_if_orphan(pruning: Optional[Pruning]):
    """
    :return: True if the pruning has been deleted
    """
    if not pruning:
        return True

    if not pruning.scrapings.exists():
        print(f'deleting not validated moderation for pruning {pruning} since it has no scraping '
              f'any more')
        PruningModeration.objects.filter(pruning=pruning, validated_at__isnull=True).delete()
        ParsingModeration.objects.filter(parsing__prunings=pruning, validated_at__isnull=True)\
            .delete()
        return True

    return False

######################
# QUALITY EVALUATION #
######################


def page_first_pruning_was_validated(page: Page) -> Optional[bool]:
    for page_version in page.history.all():
        if page_version.pruning_validation_counter == -1:
            return False

        if page_version.pruning_validation_counter > 0:
            return True

    return None
