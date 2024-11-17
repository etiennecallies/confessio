from typing import Optional

from home.models import Page, Scraping
from scraping.services.page_service import delete_scraping
from scraping.services.prune_scraping_service import prune_pruning, \
    create_pruning


def is_extracted_html_list_identical_for_scraping(scraping: Scraping,
                                                  extracted_html_list: list[str]) -> bool:
    prunings = scraping.prunings.all()
    if not prunings and not extracted_html_list:
        return True

    if not prunings or not extracted_html_list:
        return False

    return set(p.extracted_html for p in prunings) == set(extracted_html_list)


def upsert_scraping(page: Page, extracted_html: Optional[str]) -> ():
    extracted_html_list = [extracted_html] if extracted_html else []  # TODO adapt this

    # Compare result to last scraping
    scraping = page.get_latest_scraping()
    if (scraping is not None
            and is_extracted_html_list_identical_for_scraping(scraping, extracted_html_list)):
        # If a scraping exists and is identical to last one
        scraping.nb_iterations += 1
        scraping.save()

        for pruning in scraping.prunings.all():
            prune_pruning(pruning)
    else:
        if scraping is not None:
            # If a scraping exists and is different from last one, we delete it
            delete_scraping(scraping)

        prunings = []
        for extracted_html_item in extracted_html_list:
            prunings.append(create_pruning(extracted_html_item))

        scraping = Scraping(
            nb_iterations=1,
            page=page,
        )
        scraping.save()

        for pruning in prunings:
            scraping.prunings.add(pruning)
            prune_pruning(pruning)
