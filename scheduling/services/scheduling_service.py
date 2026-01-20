from dataclasses import dataclass, field
from uuid import UUID

from django.db.models import Q, Subquery

from attaching.models import Image
from home.models import Pruning, Website
from home.models import Scraping
from scheduling.models import Scheduling
from scheduling.models.parsing_models import ParsingModeration, Parsing


def get_scheduling_parsings(scheduling: Scheduling) -> list[Parsing]:
    all_parsings = []
    for pruning_parsing in scheduling.pruning_parsings.all():
        parsing_history_id = pruning_parsing.parsing_history_id
        historical_parsing = Parsing.history.get(history_id=parsing_history_id)
        parsing = historical_parsing.instance
        all_parsings.append(parsing)

    return all_parsings


@dataclass
class SchedulingPruningsAndParsings:
    scrapings: list[Scraping] = field(default_factory=list)
    images: list[Image] = field(default_factory=list)
    prunings_by_scraping_uuid: dict[UUID, list[Pruning]] = field(default_factory=dict)
    prunings_by_image_uuid: dict[UUID, list[Pruning]] = field(default_factory=dict)
    parsing_by_pruning_uuid: dict[UUID, Parsing] = field(default_factory=dict)


def get_pruning_by_history_id(pruning_history_id: int,
                              pruning_by_history_id: dict[int, Pruning]) -> Pruning:
    if pruning_history_id in pruning_by_history_id:
        return pruning_by_history_id[pruning_history_id]

    historical_pruning = Pruning.history.get(history_id=pruning_history_id)
    pruning = historical_pruning.instance
    pruning_by_history_id[pruning_history_id] = pruning
    return pruning


def get_scheduling_prunings_and_parsings(scheduling: Scheduling) -> SchedulingPruningsAndParsings:
    pruning_by_history_id = {}

    parsing_by_pruning_uuid = {}
    for pruning_parsing in scheduling.pruning_parsings.all():
        parsing_history_id = pruning_parsing.parsing_history_id
        historical_parsing = Parsing.history.get(history_id=parsing_history_id)
        parsing = historical_parsing.instance
        pruning = get_pruning_by_history_id(pruning_parsing.pruning_history_id,
                                            pruning_by_history_id)
        parsing_by_pruning_uuid[pruning.uuid] = parsing

    scrapings = []
    scraping_by_history_id = {}
    for historical_scraping in scheduling.historical_scrapings.all():
        scraping_history_id = historical_scraping.scraping_history_id
        historical_scraping = Scraping.history.get(history_id=scraping_history_id)
        scraping = historical_scraping.instance
        scraping_by_history_id[scraping_history_id] = scraping
        scrapings.append(scraping)

    prunings_by_scraping_uuid = {}
    for scraping_pruning in scheduling.scraping_prunings.all():
        scraping_history_id = scraping_pruning.scraping_history_id
        scraping = scraping_by_history_id[scraping_history_id]
        pruning = get_pruning_by_history_id(scraping_pruning.pruning_history_id,
                                            pruning_by_history_id)
        prunings_by_scraping_uuid.setdefault(scraping.uuid, []).append(pruning)

    images = []
    image_by_history_id = {}
    for historical_image in scheduling.historical_images.all():
        image_history_id = historical_image.image_history_id
        historical_image = Image.history.get(history_id=image_history_id)
        image = historical_image.instance
        image_by_history_id[image_history_id] = image
        images.append(image)

    prunings_by_image_uuid = {}
    for image_pruning in scheduling.image_prunings.all():
        image_history_id = image_pruning.image_history_id
        image = image_by_history_id[image_history_id]
        pruning = get_pruning_by_history_id(image_pruning.pruning_history_id,
                                            pruning_by_history_id)
        prunings_by_image_uuid.setdefault(image.uuid, []).append(pruning)

    return SchedulingPruningsAndParsings(
        scrapings=scrapings,
        images=images,
        prunings_by_scraping_uuid=prunings_by_scraping_uuid,
        prunings_by_image_uuid=prunings_by_image_uuid,
        parsing_by_pruning_uuid=parsing_by_pruning_uuid,
    )


################
# GET WEBSITES #
################

def get_websites_of_prunings(prunings: list[Pruning]) -> list[Website]:
    history_ids = Subquery(
        Pruning.history.filter(
            uuid__in=[pruning.uuid for pruning in prunings]
        ).values('history_id')
    )

    return list(
        Website.objects.filter(
            schedulings__in=Scheduling.objects.filter(
                Q(scraping_prunings__pruning_history_id__in=history_ids)
                | Q(image_prunings__pruning_history_id__in=history_ids),
                status=Scheduling.Status.INDEXED,
            )
        ).distinct()
    )


def get_websites_of_parsing(parsing: Parsing) -> list[Website]:
    history_ids = Subquery(
        parsing.history.values('history_id')
    )

    return list(
        Website.objects.filter(
            schedulings__in=Scheduling.objects.filter(
                pruning_parsings__parsing_history_id__in=history_ids,
                status=Scheduling.Status.INDEXED,
            )
        ).distinct()
    )


################
# GET PRUNINGS #
################

def get_prunings_of_parsing(parsing: Parsing) -> list[Pruning]:
    history_ids = Subquery(
        parsing.history.values('history_id')
    )

    pruning_history_ids = Subquery(
        Scheduling.objects.filter(
            pruning_parsings__parsing_history_id__in=history_ids,
            status=Scheduling.Status.INDEXED,
        ).values('pruning_parsings__pruning_history_id')
    )

    return list(
        Pruning.history.filter(
            history_id__in=pruning_history_ids
        ).distinct()
    )


def get_parsing_moderation_of_pruning(pruning: Pruning) -> ParsingModeration | None:
    history_ids = Subquery(
        pruning.history.values('history_id')
    )

    parsing_history_ids = Subquery(
        Scheduling.objects.filter(
            pruning_parsings__pruning_history_id__in=history_ids,
            status=Scheduling.Status.INDEXED,
        ).values('pruning_parsings__parsing_history_id')
    )

    parsing_uuids = Parsing.history.filter(
        history_id__in=parsing_history_ids
    ).values_list('uuid', flat=True)

    return ParsingModeration.objects.filter(
        parsing__uuid__in=parsing_uuids
    ).first()
