import asyncio
import traceback
from datetime import datetime

from background_task import background
from background_task.tasks import TaskSchedule
from django.db.models.functions import Now

from home.models import Website, Log
from home.utils.log_utils import info, start_log_buffer, get_log_buffer
from scraping.scrape.download_refine_and_extract import get_fresh_extracted_html_list
from scraping.services.crawl_website_service import crawl_website
from scraping.services.page_service import delete_page
from scraping.services.recognize_image_service import recognize_images_for_website
from scraping.services.scrape_page_service import upsert_extracted_html_list


########################
# CRAWL WEBSITE WORKER #
########################

@background(queue='main', schedule=TaskSchedule(priority=2))
def worker_crawl_website(website_uuid: str, timeout_dt: datetime | None):
    try:
        website = Website.objects.get(uuid=website_uuid)
    except Website.DoesNotExist:
        info(f'Website {website_uuid} does not exist for worker_crawl_website')
        return

    start_log_buffer()
    now = datetime.now()
    if timeout_dt and now > timeout_dt:
        info(f'Timeout reached before starting crawling, now = {now}, timeout = {timeout_dt}')
        save_buffer(website, Log.Type.CRAWLING, Log.Status.TIMEOUT)
        return

    handle_crawl_website(website)


def handle_crawl_website(website: Website):
    info(f'Starting crawling for website {website.name} {website.uuid}')

    try:
        got_pages_with_content, some_pages_visited = asyncio.run(crawl_website(website))
    except Exception:
        info(f'Exception while crawling website {website.name} {website.uuid}')
        stack_trace = traceback.format_exc()
        if len(stack_trace) > 8000:
            print(stack_trace[:4000] + '...')
            print('...' + stack_trace[-4000:])
        else:
            print(stack_trace)

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

    recognize_images_for_website(website)
    save_buffer(website, Log.Type.CRAWLING)


######################
# SCRAPE PAGE WORKER #
######################

@background(queue='main', schedule=TaskSchedule(priority=1))
def worker_scrape_page(website_uuid: str, timeout_dt: datetime | None):
    try:
        website = Website.objects.get(uuid=website_uuid)
    except Website.DoesNotExist:
        info(f'Website {website_uuid} does not exist for worker_scrape_page')
        return

    start_log_buffer()
    now = datetime.now()
    if timeout_dt and now > timeout_dt:
        info(f'Timeout reached before starting scraping, now = {now}, timeout = {timeout_dt}')
        save_buffer(website, Log.Type.SCRAPING, Log.Status.TIMEOUT)
        return

    handle_scrape_page(website)


def handle_scrape_page(website: Website):
    info(f'Starting to scrape website {website.name} {website.uuid}')

    for page in website.get_pages():
        if website.enabled_for_crawling:
            # Actually do the scraping
            extracted_html_list = asyncio.run(get_fresh_extracted_html_list(page.url))
        else:
            extracted_html_list = []

        if not extracted_html_list:
            info(f'No more content for {page.url}, deleting page {page.uuid}')
            delete_page(page)

            # Trigger a recrawl to make sure we don't miss anything
            if website.crawling and website.enabled_for_crawling:
                website.crawling.recrawl_triggered_at = Now()
                website.crawling.save()
            continue

        # Insert or update scraping
        upsert_extracted_html_list(page, extracted_html_list)
        info(f'Successfully scraped page {page.url} {page.uuid}')

    recognize_images_for_website(website)

    info(f'Successfully scraped website {website.name} {website.uuid}')
    save_buffer(website, Log.Type.SCRAPING)


#######
# LOG #
#######

def save_buffer(website: Website, log_type: Log.Type, status: Log.Status = Log.Status.DONE):
    buffer_value = get_log_buffer()
    log = Log(type=log_type,
              website=website,
              content=buffer_value,
              status=status,
              )
    log.save()
