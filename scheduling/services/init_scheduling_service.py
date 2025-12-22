from dataclasses import dataclass

from home.models import Website
from scheduling.models import Scheduling, SchedulingHistoricalChurch, \
    SchedulingHistoricalScraping, SchedulingHistoricalImage, SchedulingHistoricalOClocherMatching, \
    SchedulingHistoricalOClocherSchedule


@dataclass
class SchedulingRelatedObjects:
    church_history_ids: list[int]
    scraping_history_ids: list[int]
    image_history_ids: list[int]
    oclocher_matching_history_ids: list[int]
    oclocher_schedule_history_ids: list[int]


def get_church_history_ids(website: Website) -> list[int]:
    church_history_ids = []
    for parish in website.parishes.all():
        for church in parish.churches.all():
            church_history_ids.append(church.history.latest().history_id)

    return church_history_ids


def get_scraping_history_ids(website: Website) -> list[int]:
    # TODO implement actual logic
    return []


def get_image_history_ids(website: Website) -> list[int]:
    image_history_ids = []
    # TODO add history to image
    # for image in website.images.all():
    #     image_history_ids.append(image.history.latest().history_id)
    return image_history_ids


def get_oclocher_matching_history_ids(website: Website) -> list[int]:
    try:
        oclocher_organization = website.oclocher_organization
    except Website.oclocher_organization.RelatedObjectDoesNotExist:
        return []

    oclocher_matching = oclocher_organization.matching
    if oclocher_matching is None:
        return []

    return [oclocher_matching.history.latest().history_id]


def get_oclocher_schedule_history_ids(website: Website) -> list[int]:
    try:
        oclocher_organization = website.oclocher_organization
    except Website.oclocher_organization.RelatedObjectDoesNotExist:
        return []

    oclocher_schedule_history_ids = []
    for schedule in oclocher_organization.schedules.all():
        oclocher_schedule_history_ids.append(schedule.history.latest().history_id)

    return oclocher_schedule_history_ids


def build_scheduling(website: Website,
                     must_be_indexed_after_scheduling: Scheduling | None
                     ) -> tuple[Scheduling, SchedulingRelatedObjects]:
    scheduling = Scheduling(
        website=website,
        status=Scheduling.Status.BUILT,
        must_be_indexed_after_scheduling=must_be_indexed_after_scheduling,
    )

    church_history_ids = get_church_history_ids(website)
    scraping_history_ids = get_scraping_history_ids(website)
    image_history_ids = get_image_history_ids(website)
    oclocher_matching_history_ids = get_oclocher_matching_history_ids(website)
    oclocher_schedule_history_ids = get_oclocher_schedule_history_ids(website)

    scheduling_related_objects = SchedulingRelatedObjects(
        church_history_ids=church_history_ids,
        scraping_history_ids=scraping_history_ids,
        image_history_ids=image_history_ids,
        oclocher_matching_history_ids=oclocher_matching_history_ids,
        oclocher_schedule_history_ids=oclocher_schedule_history_ids,
    )

    return scheduling, scheduling_related_objects


def bulk_create_scheduling_related_objects(
    scheduling: Scheduling,
    scheduling_related_objects: SchedulingRelatedObjects
) -> None:
    # SchedulingHistoricalChurch
    church_objs = [
        SchedulingHistoricalChurch(
            scheduling=scheduling,
            church_history_id=church_id
        ) for church_id in scheduling_related_objects.church_history_ids
    ]
    SchedulingHistoricalChurch.objects.bulk_create(church_objs)

    # SchedulingHistoricalScraping
    scraping_objs = [
        SchedulingHistoricalScraping(
            scheduling=scheduling,
            scraping_history_id=scraping_id
        ) for scraping_id in scheduling_related_objects.scraping_history_ids
    ]
    SchedulingHistoricalScraping.objects.bulk_create(scraping_objs)

    # SchedulingHistoricalImage
    image_objs = [
        SchedulingHistoricalImage(
            scheduling=scheduling,
            image_history_id=image_id
        ) for image_id in scheduling_related_objects.image_history_ids
    ]
    SchedulingHistoricalImage.objects.bulk_create(image_objs)

    # SchedulingHistoricalOClocherMatching
    oclocher_matching_objs = [
        SchedulingHistoricalOClocherMatching(
            scheduling=scheduling,
            oclocher_matching_history_id=matching_id
        ) for matching_id in scheduling_related_objects.oclocher_matching_history_ids
    ]
    SchedulingHistoricalOClocherMatching.objects.bulk_create(oclocher_matching_objs)

    # SchedulingHistoricalOClocherSchedule
    oclocher_schedule_objs = [
        SchedulingHistoricalOClocherSchedule(
            scheduling=scheduling,
            oclocher_schedule_history_id=schedule_id
        ) for schedule_id in scheduling_related_objects.oclocher_schedule_history_ids
    ]
    SchedulingHistoricalOClocherSchedule.objects.bulk_create(oclocher_schedule_objs)
