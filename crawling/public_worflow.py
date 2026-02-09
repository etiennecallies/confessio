from crawling.workflows.download.download_content import redirects_to_other_url, \
    get_content_from_url
from crawling.workflows.scrape.download_refine_and_extract import get_extracted_html_list


######################
# REFINE AND EXTRACT #
######################

def crawling_get_extracted_html_list(html_content: str) -> list[str] | None:
    return get_extracted_html_list(html_content)


###################
# URL REDIRECTION #
###################

def ccrawling_redirects_to_other_url(url1: str, url2: str) -> bool:
    return redirects_to_other_url(url1, url2)


############
# DOWNLOAD #
############

def crawling_get_content_from_url(url: str) -> str | None:
    return get_content_from_url(url)
