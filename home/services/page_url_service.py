from home.models import Page
from scraping.refine.refine_content import get_text_if_not_table


def get_page_url_with_pointer(page: Page):
    latest_pruning = page.get_latest_pruning()

    pointer_text = None
    if latest_pruning and latest_pruning.pruned_html:
        first_line = latest_pruning.pruned_html.split('<br>\n')[0]
        pointer_text = get_text_if_not_table(first_line)

    if pointer_text is None:
        return page.url

    return f'{page.url}#:~:text={pointer_text.strip()}'
