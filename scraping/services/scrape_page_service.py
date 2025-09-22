from home.models import Page, Scraping
from scraping.services.page_service import delete_scraping, check_for_orphan_prunings
from scraping.services.prune_scraping_service import create_pruning, prune_pruning
from scraping.utils.ram_utils import print_memory_usage


def is_extracted_html_list_identical_for_scraping(scraping: Scraping,
                                                  extracted_html_list: list[str]) -> bool:
    prunings = scraping.prunings.all()
    if not prunings and not extracted_html_list:
        return True

    if not prunings or not extracted_html_list:
        return False

    return set(p.extracted_html for p in prunings) == set(extracted_html_list)


def upsert_extracted_html_list(page: Page, extracted_html_list: list[str]):
    prunings_to_prune = []
    old_prunings = []
    print_memory_usage('begin upsert_extracted_html_list')

    # Compare result to last scraping
    if (page.has_been_scraped()
            and is_extracted_html_list_identical_for_scraping(page.scraping,
                                                              extracted_html_list)):
        # If a scraping exists and is identical to last one
        page.scraping.nb_iterations += 1
        page.scraping.save()

        print_memory_usage('before appending prunings')

        for pruning in page.scraping.prunings.all():
            prunings_to_prune.append(pruning)
    else:
        for extracted_html_item in extracted_html_list:
            prunings_to_prune.append(create_pruning(extracted_html_item))

        print_memory_usage('after create_pruning')

        if page.has_been_scraped():
            old_prunings = list(page.scraping.prunings.all())
            page.scraping.delete()

        scraping = Scraping(
            nb_iterations=1,
            page=page,
        )
        scraping.save()

        print_memory_usage('after scraping.save()')

        for pruning in prunings_to_prune:
            scraping.prunings.add(pruning)

    print_memory_usage('before prune_pruning')

    for pruning in prunings_to_prune:
        prune_pruning(pruning)

    print_memory_usage('before check_for_orphan_prunings')

    if old_prunings:
        check_for_orphan_prunings(old_prunings, page.website)

    print_memory_usage('end upsert_extracted_html_list')


def delete_orphan_scrapings() -> int:
    delete_count = 0
    for scraping in Scraping.objects.filter(page__isnull=True):
        delete_scraping(scraping)
        delete_count += 1

    return delete_count
