from typing import Type

from django.db.models import Q, Model

from core.management.abstract_command import AbstractCommand


class AbstractCleaningCommand(AbstractCommand):

    def delete_objects(self, objects):
        counter = 0
        for obj in objects:
            obj.delete()
            counter += 1
        return counter

    def clean_history(self, model: Type[Model], history_model: Type[Model]):
        self.info(f'Starting cleaning {model.__name__} history items')
        query = history_model.objects.filter(
            ~Q(uuid__in=model.objects.values_list('uuid', flat=True)))
        counter = query.count()
        query.delete()
        self.success(
            f'Done removing {counter} orphan {model.__name__} history items')

    @staticmethod
    def get_changed_fields(fields_to_consider: set[str], old, new):
        """Return the set of fields that differ between two records."""
        diff = set()
        for field in fields_to_consider:
            if getattr(old, field) != getattr(new, field):
                diff.add(field)
        return diff

    def delete_irrelevant_history(
            self, model: Type[Model], fields_to_ignore: set[str]):
        total_deleted = 0
        self.info(
            f'Starting deleting irrelevant {model.__name__} history items')

        fields = {f.name for f in model._meta.fields}
        fields_to_consider = fields - fields_to_ignore

        for obj in model.objects.all().iterator():
            history = list(obj.history.order_by('history_date'))

            if len(history) < 2:
                continue

            for prev, current in zip(history, history[1:]):
                if current.history_type in ['+', '-']:
                    continue

                changed_fields = self.get_changed_fields(
                    fields_to_consider, prev, current)

                if not changed_fields or all(
                        f in fields_to_ignore for f in changed_fields):
                    current.delete()
                    total_deleted += 1

        self.success(
            f"Deleted {total_deleted} irrelevant "
            f"{model.__name__} history items.")
