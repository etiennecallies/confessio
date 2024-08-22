from typing import Optional

from home.models import Page, Pruning, Scraping, PruningModeration


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
        return True

    return False
