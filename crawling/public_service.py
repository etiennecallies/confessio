from crawling.tasks import worker_crawl_website
from registry.models import Website


def crawling_crawl_website(website: Website):
    worker_crawl_website(str(website.uuid), None)
