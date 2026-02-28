from crawling.models import Scraping
from crawling.services.scraping_service import check_for_orphan_prunings
from registry.models import Website
from scheduling.public_service import scheduling_create_pruning


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
        # If scraping is identical to last one, we let it as is
        return

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
        url=url,
        website=website,
    )
    scraping.save()

    for extracted_html_item in extracted_html_list:
        scraping.prunings.add(scheduling_create_pruning(extracted_html_item))
