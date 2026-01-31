from crawling.models import Scraping
from registry.models import Website
from scraping.services.prune_scraping_service import create_pruning
from scraping.services.scraping_service import check_for_orphan_prunings


def is_extracted_html_list_identical_for_scraping(scraping: Scraping,
                                                  extracted_html_list: list[str]) -> bool:
    prunings = scraping.prunings.all()
    if not prunings and not extracted_html_list:
        return True

    if not prunings or not extracted_html_list:
        return False

    return set(p.extracted_html for p in prunings) == set(extracted_html_list)


def upsert_extracted_html_list(scraping: Scraping, extracted_html_list: list[str]):
    # Compare result to last scraping
    if is_extracted_html_list_identical_for_scraping(scraping, extracted_html_list):
        # If a scraping exists and is identical to last one
        scraping.nb_iterations += 1
        scraping.save()
    else:
        old_prunings = list(scraping.prunings.all())
        url = scraping.url
        website = scraping.website
        scraping.delete()

        create_scraping(extracted_html_list, url, website)

        if old_prunings:
            check_for_orphan_prunings(old_prunings)


def create_scraping(extracted_html_list: list[str],
                    url: str,
                    website: Website) -> None:
    scraping = Scraping(
        nb_iterations=1,
        url=url,
        website=website,
    )
    scraping.save()

    for extracted_html_item in extracted_html_list:
        scraping.prunings.add(create_pruning(extracted_html_item))
