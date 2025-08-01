from home.models import Page, Scraping, Pruning
from scraping.services.page_service import delete_scraping
from scraping.services.prune_scraping_service import create_pruning


def is_extracted_html_list_identical_for_scraping(scraping: Scraping,
                                                  extracted_html_list: list[str]) -> bool:
    prunings = scraping.prunings.all()
    if not prunings and not extracted_html_list:
        return True

    if not prunings or not extracted_html_list:
        return False

    return set(p.extracted_html for p in prunings) == set(extracted_html_list)


def upsert_extracted_html_list(page: Page, extracted_html_list: list[str]
                               ) -> list[Pruning]:
    prunings_to_prune = []

    # Compare result to last scraping
    if (page.has_been_scraped()
            and is_extracted_html_list_identical_for_scraping(page.scraping,
                                                              extracted_html_list)):
        # If a scraping exists and is identical to last one
        page.scraping.nb_iterations += 1
        page.scraping.save()

        for pruning in page.scraping.prunings.all():
            prunings_to_prune.append(pruning)
    else:
        if page.has_been_scraped():
            # If a scraping exists and is different from last one, we delete it
            delete_scraping(page.scraping)

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
            prunings_to_prune.append(pruning)

    return prunings_to_prune


def delete_orphan_scrapings() -> int:
    delete_count = 0
    for scraping in Scraping.objects.filter(page__isnull=True):
        delete_scraping(scraping)
        delete_count += 1

    return delete_count
