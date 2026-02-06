from crawling.workflows.scrape.download_refine_and_extract import get_extracted_html_list


def crawling_get_extracted_html_list(html_content: str) -> list[str] | None:
    return get_extracted_html_list(html_content)
