from home.models import Page
from scraping.refine.refine_content import get_text_if_not_table


def get_page_url_with_pointer(page: Page):
    latest_scraping = page.get_latest_scraping()

    pointer_text = None
    if latest_scraping and latest_scraping.confession_html_pruned:
        first_line = latest_scraping.confession_html_pruned.split('<br>\n')[0]
        pointer_text = get_text_if_not_table(first_line)

    if pointer_text is None:
        return page.url

    return f'{page.url}#:~:text={pointer_text}'
