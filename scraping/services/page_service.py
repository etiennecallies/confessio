from typing import Optional, Literal

from home.models import Page, Pruning, Scraping, PruningModeration, ParsingModeration


############
# DELETION #
############

def delete_page(page: Page):
    prunings = page.get_prunings()
    page.delete()

    if not prunings:
        return

    for pruning in prunings:
        remove_pruning_if_orphan(pruning)


def delete_scraping(scraping: Scraping):
    prunings = scraping.prunings.all()
    scraping.delete()
    for pruning in prunings:
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
