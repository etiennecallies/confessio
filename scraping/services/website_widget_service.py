from home.models import Website
from scraping.crawl.download_and_search_urls import CrawlingResult


def process_extracted_widgets(website: Website, crawling_result: CrawlingResult):
    if not crawling_result.widgets_by_url:
        return

    print(crawling_result.widgets_by_url)
