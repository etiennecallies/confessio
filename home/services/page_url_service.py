from home.models import Page, Pruning
from scraping.extract.split_content import split_and_tag
from scraping.prune.action_interfaces import DummyActionInterface
from scraping.refine.refine_content import get_text_if_not_table


def get_page_url_with_pointer_at_pruning(page: Page, pruning: Pruning):
    pointer_text = None
    if pruning and pruning.pruned_indices:
        first_index = pruning.pruned_indices[0]
        line_and_tags = split_and_tag(pruning.extracted_html, DummyActionInterface())
        assert len(line_and_tags) > first_index, f'Index {first_index} out of range'
        line_and_tag = line_and_tags[first_index]
        pointer_text = get_text_if_not_table(line_and_tag.line_without_link)

    if pointer_text is None:
        return page.url

    return f'{page.url}#:~:text={pointer_text.strip()}'
