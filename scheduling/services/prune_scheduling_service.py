from dataclasses import dataclass

from home.models import Scraping, Image
from scheduling.models import Scheduling, ScrapingPruning, ImagePruning
from scraping.services.prune_scraping_service import prune_pruning


@dataclass
class SchedulingPruningObjects:
    scraping_pruning_history_ids: list[tuple[int, int]]
    image_pruning_history_ids: list[tuple[int, int]]


def do_prune_scheduling(scheduling: Scheduling) -> SchedulingPruningObjects:
    scraping_pruning_history_ids = []
    for scheduling_historical_scraping in scheduling.historical_scrapings.all():
        scraping_history_id = scheduling_historical_scraping.scraping_history_id
        historical_scraping = Scraping.history.get(history_id=scraping_history_id)
        scraping = historical_scraping.instance

        for pruning in scraping.prunings.all():
            prune_pruning(pruning)

            pruning_history_id = pruning.history.latest().history_id
            scraping_pruning_history_ids.append((scraping_history_id, pruning_history_id))

    image_pruning_history_ids = []
    for scheduling_historical_image in scheduling.historical_images.all():
        image_history_id = scheduling_historical_image.image_history_id
        historical_image = Image.history.get(history_id=image_history_id)
        image = historical_image.instance

        for pruning in image.prunings.all():
            prune_pruning(pruning)

            pruning_history_id = pruning.history.latest().history_id
            image_pruning_history_ids.append((image_history_id, pruning_history_id))

    return SchedulingPruningObjects(
        scraping_pruning_history_ids=scraping_pruning_history_ids,
        image_pruning_history_ids=image_pruning_history_ids,
    )


def bulk_create_scheduling_pruning_objects(
        scheduling: Scheduling,
        scheduling_pruning_objects: SchedulingPruningObjects):
    # ScrapingPruning
    scraping_objs = [
        ScrapingPruning(
            scheduling=scheduling,
            scraping_history_id=scraping_history_id,
            pruning_history_id=pruning_history_id,
        ) for scraping_history_id, pruning_history_id
        in scheduling_pruning_objects.scraping_pruning_history_ids
    ]
    ScrapingPruning.objects.bulk_create(scraping_objs)

    # ImagePruning
    image_objs = [
        ImagePruning(
            scheduling=scheduling,
            image_history_id=image_history_id,
            pruning_history_id=pruning_history_id,
        ) for image_history_id, pruning_history_id
        in scheduling_pruning_objects.image_pruning_history_ids
    ]
    ImagePruning.objects.bulk_create(image_objs)
