from home.models import Page, Pruning
from scraping.extract.split_content import split_lines
from scraping.refine.refine_content import get_text_if_not_table, remove_link_from_html


def get_page_url_with_pointer_at_pruning(page: Page, pruning: Pruning):
    pointer_text = None
    if pruning and pruning.pruned_indices:
        first_index = pruning.pruned_indices[0]
        lines = split_lines(pruning.extracted_html)
        assert len(lines) > first_index, f'Index {first_index} out of range'
        first_line = lines[first_index]
        first_line_without_link = remove_link_from_html(first_line)
        pointer_text = get_text_if_not_table(first_line_without_link)

    if pointer_text is None:
        return page.url

    return f'{page.url}#:~:text={pointer_text.strip()}'
