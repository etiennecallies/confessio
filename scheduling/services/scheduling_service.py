from dataclasses import dataclass
from uuid import UUID

from home.models import Parsing, Pruning, Scraping, Image
from scheduling.models import Scheduling


def get_scheduling_parsings(scheduling: Scheduling) -> list[Parsing]:
    all_parsings = []
    for pruning_parsing in scheduling.pruning_parsings.all():
        parsing_history_id = pruning_parsing.parsing_history_id
        historical_parsing = Parsing.history.get(history_id=parsing_history_id)
        parsing = historical_parsing.instance
        all_parsings.append(parsing)

    return all_parsings


@dataclass
class SchedulingParsingsAndPrunings:
    parsings: list[Parsing]
    prunings_by_parsing_uuid: dict[UUID, list[Pruning]]
    scrapings_by_parsing_uuid: dict[UUID, list[Scraping]]
    images_by_parsing_uuid: dict[UUID, list[Image]]


def get_scheduling_parsings_and_prunings(scheduling: Scheduling) -> SchedulingParsingsAndPrunings:
    parsings = []
    prunings_by_parsing_uuid = {}
    parsing_by_pruning_history_id = {}
    for pruning_parsing in scheduling.pruning_parsings.all():
        parsing_history_id = pruning_parsing.parsing_history_id
        historical_parsing = Parsing.history.get(history_id=parsing_history_id)
        parsing = historical_parsing.instance
        parsings.append(parsing)

        pruning_history_id = pruning_parsing.pruning_history_id
        historical_pruning = Pruning.history.get(history_id=pruning_history_id)
        pruning = historical_pruning.instance
        prunings_by_parsing_uuid.setdefault(parsing.uuid, []).append(pruning)
        parsing_by_pruning_history_id[pruning_history_id] = parsing

    scrapings_by_parsing_uuid = {}
    for scraping_pruning in scheduling.scraping_prunings.all():
        scraping_history_id = scraping_pruning.scraping_history_id
        historical_scraping = Scraping.history.get(history_id=scraping_history_id)
        scraping = historical_scraping.instance
        parsing = parsing_by_pruning_history_id.get(scraping_pruning.pruning_history_id, None)
        if parsing is not None:
            scrapings_by_parsing_uuid.setdefault(parsing.uuid, []).append(scraping)

    images_by_parsing_uuid = {}
    for image_pruning in scheduling.image_prunings.all():
        image_history_id = image_pruning.image_history_id
        historical_image = Image.history.get(history_id=image_history_id)
        image = historical_image.instance
        parsing = parsing_by_pruning_history_id.get(image_pruning.pruning_history_id, None)
        if parsing is not None:
            images_by_parsing_uuid.setdefault(parsing.uuid, []).append(image)

    return SchedulingParsingsAndPrunings(
        parsings=parsings,
        prunings_by_parsing_uuid=prunings_by_parsing_uuid,
        scrapings_by_parsing_uuid=scrapings_by_parsing_uuid,
        images_by_parsing_uuid=images_by_parsing_uuid,
    )
