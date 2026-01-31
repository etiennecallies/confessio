from crawling.models import Scraping
from core.utils.log_utils import info
from scheduling.models.pruning_models import Pruning
from scheduling.services.prune_scraping_service import remove_pruning_moderation_if_orphan


############
# DELETION #
############

def delete_scraping(scraping: Scraping):
    info(f'deleting scraping {scraping} of website {scraping.website.uuid}')
    # save prunings to delete
    prunings = list(scraping.prunings.all())

    scraping.delete()
    check_for_orphan_prunings(prunings)


def check_for_orphan_prunings(prunings: list[Pruning]):
    for pruning in prunings:
        remove_pruning_moderation_if_orphan(pruning)
