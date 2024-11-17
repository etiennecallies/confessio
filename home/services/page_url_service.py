from home.models import Page, Pruning
from scraping.refine.refine_content import get_text_if_not_table


def get_page_url_with_pointer_at_pruning(page: Page, pruning: Pruning):
    pointer_text = None
    if pruning and pruning.pruned_html:
        first_line = pruning.pruned_html.split('<br>\n')[0]
        pointer_text = get_text_if_not_table(first_line)

    if pointer_text is None:
        return page.url

    return f'{page.url}#:~:text={pointer_text.strip()}'
