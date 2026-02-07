from django.db.models.functions import Now

from core.utils.log_utils import info, log_stack_trace
from crawling.models import Log, CrawlingModeration
from crawling.services.crawl_website_service import crawl_website
from crawling.services.log_service import save_buffer
from crawling.services.scrape_scraping_service import upsert_extracted_html_list
from crawling.services.scraping_service import delete_scraping
from crawling.workflows.scrape.download_refine_and_extract import get_fresh_extracted_html_list
from registry.models import Website
from scheduling.public_service import scheduling_init_scheduling


########################
# CRAWL WEBSITE WORKER #
########################

def handle_crawl_website(website: Website):
    info(f'Starting crawling for website {website.name} {website.uuid}')

    try:
        crawling_category = crawl_website(website)
    except Exception:
        info(f'Exception while crawling website {website.name} {website.uuid}')
        log_stack_trace()

        save_buffer(website, Log.Type.CRAWLING, Log.Status.FAILURE)
        return

    if not website.enabled_for_crawling:
        info(f'Website {website.name} {website.uuid} is not enabled for crawling.')
    elif crawling_category == CrawlingModeration.Category.OK:
        info(f'Successfully crawled website {website.name} {website.uuid}')
    elif crawling_category == CrawlingModeration.Category.NO_PAGE:
        info(f'No page found for website {website.name} {website.uuid}')
    else:
        info(f'Error while crawling website {website.name} {website.uuid}')
        if website.crawling:
            info(website.crawling.error_detail)
        else:
            info('No crawling found')

    scheduling_init_scheduling(website)
    save_buffer(website, Log.Type.CRAWLING)


######################
# SCRAPE PAGE WORKER #
######################

def handle_scrape_page(website: Website):
    info(f'Starting to scrape website {website.name} {website.uuid}')

    for scraping in website.scrapings.all():
        if website.enabled_for_crawling:
            # Actually do the scraping
            extracted_html_list = get_fresh_extracted_html_list(scraping.url)
        else:
            extracted_html_list = []

        if not extracted_html_list:
            info(f'No more content for {scraping.url}, deleting scraping {scraping.uuid}')
            delete_scraping(scraping)

            # Trigger a recrawl to make sure we don't miss anything
            if website.crawling and website.enabled_for_crawling:
                website.crawling.recrawl_triggered_at = Now()
                website.crawling.save()
            continue

        # Insert or update scraping
        upsert_extracted_html_list(scraping, extracted_html_list)
        info(f'Successfully scraped scraping {scraping.url} {scraping.uuid}')

    scheduling_init_scheduling(website)

    info(f'Successfully scraped website {website.name} {website.uuid}')
    save_buffer(website, Log.Type.SCRAPING)
