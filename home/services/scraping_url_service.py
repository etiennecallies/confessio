from urllib.parse import quote, unquote

from home.models import Scraping
from scheduling.models.pruning_models import Pruning
from scheduling.services.scheduling_service import SchedulingPrimarySources
from scraping.extract.split_content import split_lines
from scraping.refine.refine_content import get_text_if_not_table


def get_scraping_url_with_pointer_at_pruning(scraping: Scraping, pruning: Pruning):
    if scraping.url.endswith('.pdf'):
        return scraping.url

    pointer_text = None
    if pruning and pruning.get_pruned_indices():
        first_index = pruning.get_pruned_indices()[0]
        lines = split_lines(pruning.extracted_html)
        assert len(lines) > first_index, f'Index {first_index} out of range'
        first_line = lines[first_index]
        pointer_text = get_text_if_not_table(first_line)

    if pointer_text is None:
        return scraping.url

    return f'{scraping.url}#:~:text={pointer_text.strip()}'


def get_scraping_parsing_urls(scheduling_prunings_and_parsings: SchedulingPrimarySources,
                              ) -> dict[str, dict[str, str]]:
    scraping_parsing_urls = {}
    for scraping in scheduling_prunings_and_parsings.scrapings:
        prunings = scheduling_prunings_and_parsings.prunings_by_scraping_uuid[scraping.uuid]
        for pruning in prunings:
            parsing = scheduling_prunings_and_parsings.parsing_by_pruning_uuid.get(pruning.uuid)
            if not parsing:
                continue

            url = get_scraping_url_with_pointer_at_pruning(scraping, pruning)
            scraping_parsing_urls.setdefault(scraping.uuid, {})[parsing.uuid] = url

    return scraping_parsing_urls


def quote_path(path: str) -> str:
    return quote(path, safe='')


def unquote_path(path: str) -> str:
    return unquote(path)
