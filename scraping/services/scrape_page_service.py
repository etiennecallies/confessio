from typing import Optional

from home.models import Page, Scraping
from scraping.services.page_service import delete_scraping
from scraping.services.prune_scraping_service import prune_pruning, \
    create_pruning


def upsert_scraping(page: Page, extracted_html: Optional[str]) -> ():
    # Compare result to last scraping
    scraping = page.get_latest_scraping()
    if (scraping is not None
            and ((scraping.pruning is None
                  and extracted_html is None)
                 or (scraping.pruning is not None
                     and scraping.pruning.extracted_html == extracted_html))):
        # If a scraping exists and is identical to last one
        scraping.nb_iterations += 1
        scraping.save()

        if scraping.pruning is not None:
            prune_pruning(scraping.pruning)
    else:
        if scraping is not None:
            # If a scraping exists and is different from last one, we delete it
            delete_scraping(scraping)

        pruning = create_pruning(extracted_html)

        scraping = Scraping(
            nb_iterations=1,
            page=page,
            pruning=pruning,
        )
        scraping.save()

        prune_pruning(pruning)
