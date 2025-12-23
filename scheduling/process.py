from django.db import transaction
from django.db.models.functions import Now

from home.models import Website
from scheduling.models import Scheduling
from scheduling.services.index_scheduling_service import do_index_scheduling
from scheduling.services.init_scheduling_service import build_scheduling, \
    bulk_create_scheduling_related_objects
from scheduling.services.parse_scheduling_service import do_parse_scheduling
from scheduling.services.prune_scheduling_service import do_prune_scheduling, \
    bulk_create_scheduling_pruning_objects


def init_scheduling(website: Website,
                    must_be_indexed_after_scheduling: Scheduling | None = None) -> Scheduling:
    print(f"Initializing scheduling for website {website}.")

    new_scheduling, scheduling_related_objects = \
        build_scheduling(website, must_be_indexed_after_scheduling)
    with transaction.atomic():
        # Cancel any existing in-progress Scheduling for this website
        Scheduling.objects.filter(
            website=website,
            status__in=[Scheduling.Status.BUILT, Scheduling.Status.PRUNED, Scheduling.Status.PARSED]
        ).update(
            status=Scheduling.Status.CANCELLED,
            updated_at=Now(),
        )

        # Save new Scheduling
        new_scheduling.save()

        # Bulk create related objects
        bulk_create_scheduling_related_objects(new_scheduling, scheduling_related_objects)

    return new_scheduling


def prune_scheduling(scheduling: Scheduling):
    print("Pruning scheduling.")
    if scheduling.status != Scheduling.Status.BUILT:
        print(f"Scheduling is in status {scheduling.status}; skipping pruning.")
        return

    scheduling_pruning_objects = do_prune_scheduling(scheduling)

    with transaction.atomic():
        # 1. Verify the scheduling is still in BUILT status
        try:
            scheduling = Scheduling.objects.select_for_update().get(
                uuid=scheduling.uuid,
                status=Scheduling.Status.BUILT
            )
        except Scheduling.DoesNotExist:
            print("Aborting: Scheduling not found or status changed.")
            return

        # 2. Save pruning objects
        bulk_create_scheduling_pruning_objects(scheduling, scheduling_pruning_objects)

        # 3. Mark scheduling as PRUNED
        scheduling.status = Scheduling.Status.PRUNED
        scheduling.save()


def parse_scheduling(scheduling: Scheduling):
    print("Parsing scheduling.")
    if scheduling.status != Scheduling.Status.PRUNED:
        print(f"Scheduling is in status {scheduling.status}; skipping parsing.")
        return

    do_parse_scheduling(scheduling)

    Scheduling.objects.filter(
        uuid=scheduling.uuid,
        status=Scheduling.Status.PRUNED,
    ).update(
        status=Scheduling.Status.PARSED,
        updated_at=Now(),
    )


def index_scheduling(scheduling: Scheduling):
    print("Indexing scheduling.")

    if scheduling.status != Scheduling.Status.PARSED:
        print(f"Scheduling is in status {scheduling.status}; skipping indexing.")
        return

    index_events = do_index_scheduling(scheduling)

    with transaction.atomic():
        # 1. Verify the scheduling is still in PARSED status
        try:
            scheduling = Scheduling.objects.select_for_update().get(
                uuid=scheduling.uuid,
                status=Scheduling.Status.PARSED
            )
        except Scheduling.DoesNotExist:
            print("Aborting: Scheduling not found or status changed.")
            return

        # 2. Delete previous INDEXED schedulings for the same website
        # This will cascade delete related indexed events
        Scheduling.objects.filter(
            website=scheduling.website,
            status=Scheduling.Status.INDEXED,
        ).delete()

        # 3. Save index events
        for index_event in index_events:
            index_event.save()

        # 4. Mark scheduling as INDEXED
        scheduling.status = Scheduling.Status.INDEXED
        scheduling.save()


def delete_cancelled_scheduling(scheduling: Scheduling):
    print("Deleting cancelled scheduling.")

    if scheduling.status != Scheduling.Status.CANCELLED:
        print("Scheduling is not cancelled; skipping deletion.")
        return

    scheduling.delete()
