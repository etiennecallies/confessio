from typing import Optional

from home.models import Page, Pruning


def delete_page(page: Page):
    pruning = page.get_latest_pruning()
    page.delete()
    remove_pruning_if_orphan(pruning)


def remove_pruning_if_orphan(pruning: Optional[Pruning]):
    """
    :return: True if the pruning has been deleted
    """
    if not pruning:
        return True

    if not pruning.scrapings.exists():
        print(f'deleting pruning {pruning} since it has no scraping any more')
        pruning.delete()
        return True

    return False
