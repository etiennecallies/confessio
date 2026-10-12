from django.db import transaction

from attaching.models import FileNote, FileNoteModeration
from core.management.abstract_command import AbstractCommand


class Command(AbstractCommand):
    help = "Create the history of the file notes backfilled by bulk_create, which skips it."

    def handle(self, *args, **options):
        with transaction.atomic():
            for model in [FileNote, FileNoteModeration]:
                self.create_missing_history(model)

    def create_missing_history(self, model):
        # populate_history would skip the whole model, as some rows already have history
        historized_uuids = model.history.values('uuid')
        objs = list(model.objects.exclude(uuid__in=historized_uuids))
        for obj in objs:
            obj._history_date = obj.updated_at
        model.history.bulk_history_create(objs, batch_size=1000)
        self.success(f'Created {len(objs)} {model.__name__} history rows')
