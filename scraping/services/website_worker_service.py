import time

from background_task import background
from background_task.tasks import TaskSchedule
from django.db.models.functions import Now

from crawling.models import Log
from registry.models import Website
from crawling.services.log_service import save_buffer
from home.utils.log_utils import info, start_log_buffer, log_stack_trace
from scheduling.process import init_scheduling
from scraping.scrape.download_refine_and_extract import get_fresh_extracted_html_list
from scraping.services.crawl_website_service import crawl_website
from scraping.services.scraping_service import delete_scraping
from scraping.services.scrape_scraping_service import upsert_extracted_html_list


########################
# CRAWL WEBSITE WORKER #
########################

@background(queue='main', schedule=TaskSchedule(priority=2))
def worker_crawl_website(website_uuid: str, timeout_ts: int | None):
    try:
        website = Website.objects.get(uuid=website_uuid)
    except Website.DoesNotExist:
        info(f'Website {website_uuid} does not exist for worker_crawl_website')
        return

    start_log_buffer()
    now = int(time.time())
    if timeout_ts and now > timeout_ts:
        info(f'Timeout reached before starting crawling, now = {now}, timeout_ts = {timeout_ts}')
        save_buffer(website, Log.Type.CRAWLING, Log.Status.TIMEOUT)
        return

    handle_crawl_website(website)


def handle_crawl_website(website: Website):
    info(f'Starting crawling for website {website.name} {website.uuid}')

    try:
        got_pages_with_content, some_pages_visited = crawl_website(website)
    except Exception:
        info(f'Exception while crawling website {website.name} {website.uuid}')
        log_stack_trace()

        save_buffer(website, Log.Type.CRAWLING, Log.Status.FAILURE)
        return

    if not website.enabled_for_crawling:
        info(f'Website {website.name} {website.uuid} is not enabled for crawling.')
    elif got_pages_with_content:
        info(f'Successfully crawled website {website.name} {website.uuid}')
    elif some_pages_visited:
        info(f'No page found for website {website.name} {website.uuid}')
    else:
        info(f'Error while crawling website {website.name} {website.uuid}')
        if website.crawling:
            info(website.crawling.error_detail)
        else:
            info('No crawling found')

    init_scheduling(website)
    save_buffer(website, Log.Type.CRAWLING)


######################
# SCRAPE PAGE WORKER #
######################

@background(queue='main', schedule=TaskSchedule(priority=1))
def worker_scrape_page(website_uuid: str, timeout_ts: int | None):
    try:
        website = Website.objects.get(uuid=website_uuid)
    except Website.DoesNotExist:
        info(f'Website {website_uuid} does not exist for worker_scrape_page')
        return

    start_log_buffer()
    now = int(time.time())
    if timeout_ts and now > timeout_ts:
        info(f'Timeout reached before starting scraping, now = {now}, timeout_ts = {timeout_ts}')
        save_buffer(website, Log.Type.SCRAPING, Log.Status.TIMEOUT)
        return

    handle_scrape_page(website)


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

    init_scheduling(website)

    info(f'Successfully scraped website {website.name} {website.uuid}')
    save_buffer(website, Log.Type.SCRAPING)
