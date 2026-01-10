from urllib.parse import quote, unquote

from home.models import Page, Pruning
from scheduling.services.scheduling_service import SchedulingPruningsAndParsings
from scraping.extract.split_content import split_lines
from scraping.refine.refine_content import get_text_if_not_table


def get_page_url_with_pointer_at_pruning(page: Page, pruning: Pruning):
    if page.url.endswith('.pdf'):
        return page.url

    pointer_text = None
    if pruning and pruning.pruned_indices:
        first_index = pruning.pruned_indices[0]
        lines = split_lines(pruning.extracted_html)
        assert len(lines) > first_index, f'Index {first_index} out of range'
        first_line = lines[first_index]
        pointer_text = get_text_if_not_table(first_line)

    if pointer_text is None:
        return page.url

    return f'{page.url}#:~:text={pointer_text.strip()}'


def get_page_pruning_urls(scheduling_prunings_and_parsings: SchedulingPruningsAndParsings,
                          ) -> dict[str, dict[str, str]]:
    page_pruning_urls = {}
    for scraping in scheduling_prunings_and_parsings.scrapings:
        page = scraping.page
        prunings = scheduling_prunings_and_parsings.prunings_by_scraping_uuid[scraping.uuid]
        for pruning in prunings:
            parsing = scheduling_prunings_and_parsings.parsing_by_pruning_uuid.get(pruning.uuid)
            if not parsing:
                continue

            url = get_page_url_with_pointer_at_pruning(page, pruning)
            page_pruning_urls.setdefault(page.uuid, {})[parsing.uuid] = url

    return page_pruning_urls


def quote_path(path: str) -> str:
    return quote(path, safe='')


def unquote_path(path: str) -> str:
    return unquote(path)
