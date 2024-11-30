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


def upsert_extracted_html_list(page: Page, extracted_html_list: list[str]):
    # Compare result to last scraping
    latest_scraping = page.get_scraping()

    if (latest_scraping is not None
            and is_extracted_html_list_identical_for_scraping(latest_scraping,
                                                              extracted_html_list)):
        # If a scraping exists and is identical to last one
        latest_scraping.nb_iterations += 1
        latest_scraping.save()

        for pruning in latest_scraping.prunings.all():
            prune_pruning(pruning)
    else:
        if latest_scraping is not None:
            # If a scraping exists and is different from last one, we delete it
            delete_scraping(latest_scraping)

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
