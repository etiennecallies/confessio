from datetime import timedelta
from typing import Type

from background_task.models import CompletedTask
from django.db.models import Q, Model
from django.utils import timezone

from home.management.abstract_command import AbstractCommand
from home.models import Pruning, Sentence, Classifier, Page, ParsingModeration, Parsing, Log, \
    ChurchModeration, Website, WebsiteModeration
from scraping.services.page_service import delete_page
from scraping.services.parse_pruning_service import clean_parsing_moderations
from scraping.services.scrape_page_service import delete_orphan_scrapings


class Command(AbstractCommand):
    help = "Command to remove useless data from the database"

    def handle(self, *args, **options):
        self.info(f'Starting removing pages of inactive websites')
        delete_count = 0
        for page in Page.objects.filter(website__is_active=False):
            delete_page(page)
            delete_count += 1
        self.success(f'Successfully deleted {delete_count} pages')

        self.info(f'Starting cleaning orphan scrapings')
        delete_count = delete_orphan_scrapings()
        self.success(f'Successfully cleaning {delete_count} orphan scrapings')

        self.info(f'Starting cleaning old parsings')
        old_parsings = Parsing.objects.filter(website__isnull=True,
                                              human_json__isnull=True,
                                              updated_at__lt=timezone.now() - timedelta(days=30)
                                              ).all()
        counter = self.delete_objects(old_parsings)
        self.success(f'Successfully cleaned {counter} old parsings')

        self.clean_history(Parsing, Parsing.history.model)

        self.info(f'Starting cleaning parsing moderations')
        delete_count = clean_parsing_moderations()
        self.success(f'Successfully cleaning {delete_count} parsing moderations')

        self.clean_history(ParsingModeration, ParsingModeration.history.model)

        # Prunings
        self.info(f'Starting removing orphan prunings')
        orphan_prunings = Pruning.objects.filter(scrapings__isnull=True,
                                                 human_indices__isnull=True,
                                                 images__isnull=True).all()
        counter = self.delete_objects(orphan_prunings)
        self.success(f'Done removing {counter} orphan prunings')

        self.clean_history(Pruning, Pruning.history.model)

        # Sentences
        self.info(f'Starting removing orphan sentences')
        orphan_sentences = Sentence.objects.filter(prunings__isnull=True,
                                                   source__exact='ml',
                                                   human_temporal__isnull=True,
                                                   human_confession__isnull=True,
                                                   ).all()
        counter = self.delete_objects(orphan_sentences)
        self.success(f'Done removing {counter} orphan sentences')

        self.clean_history(Sentence, Sentence.history.model)

        # Classifiers
        self.info(f'Starting removing draft classifiers, older than 3 days')
        draft_classifiers = Classifier.objects.filter(
            status__exact='draft',
            created_at__lt=timezone.now() - timedelta(days=3)).all()
        counter = self.delete_objects(draft_classifiers)
        self.success(f'Done removing {counter} draft classifiers')

        self.clean_history(Classifier, Classifier.history.model)

        # Logs
        self.info(f'Starting removing old logs')
        old_logs = Log.objects.filter(
            created_at__lt=timezone.now() - timedelta(days=3)).all()
        counter = self.delete_objects(old_logs)
        self.success(f'Done removing {counter} old logs')

        # Church moderation
        self.info(f'Starting cleaning church moderation items')
        counter = 0
        for church_moderation in ChurchModeration.objects.filter(
            category=ChurchModeration.Category.LOCATION_DIFFERS,
            validated_at__isnull=True,
        ).all():
            if not church_moderation.location_desc_differs():
                church_moderation.delete()
                counter += 1
        self.success(f'Done removing {counter} church moderation items')

        # Completed tasks (background tasks)
        self.info(f'Starting removing completed tasks')
        counter = self.delete_objects(CompletedTask.objects.all())
        self.success(f'Done removing {counter} completed tasks')

        # Website history
        self.delete_irrelevant_history(Website, {
            'updated_at', 'crawling', 'nb_recent_hits', 'is_best_diocese_hit'})

        # Website moderation history
        self.delete_irrelevant_history(WebsiteModeration, {'updated_at'})

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
        self.success(f'Done removing {counter} orphan {model.__name__} history items')

    @staticmethod
    def get_changed_fields(fields_to_consider: set[str], old, new):
        """Return the set of fields that differ between two historical records."""
        diff = set()
        for field in fields_to_consider:
            if getattr(old, field) != getattr(new, field):
                diff.add(field)
        return diff

    def delete_irrelevant_history(self, model: Type[Model], fields_to_ignore: set[str]):
        total_deleted = 0
        self.info(f'Starting deleting irrelevant {model.__name__} history items')

        fields = {f.name for f in model._meta.fields}
        # fields minus ignored fields
        fields_to_consider = fields - fields_to_ignore

        for obj in model.objects.all().iterator():
            # Ordered chronologically
            history = list(obj.history.order_by('history_date'))

            # Skip if fewer than 2 versions
            if len(history) < 2:
                continue

            for prev, current in zip(history, history[1:]):
                # Skip creation/deletion markers
                if current.history_type in ['+', '-']:
                    continue

                changed_fields = self.get_changed_fields(fields_to_consider, prev, current)

                # If *only* ignored fields changed, we can delete this history record
                if not changed_fields or all(f in fields_to_ignore for f in changed_fields):
                    current.delete()
                    total_deleted += 1

        self.success(f"Deleted {total_deleted} irrelevant {model.__name__} history items.")
