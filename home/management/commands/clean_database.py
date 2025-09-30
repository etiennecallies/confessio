from datetime import timedelta
from typing import Type

from background_task.models import CompletedTask
from django.db.models import Q, Model
from django.utils import timezone

from home.management.abstract_command import AbstractCommand
from home.models import Pruning, Sentence, Classifier, Page, ParsingModeration, Parsing, Log, \
    ChurchModeration
from scraping.services.page_service import delete_page
from scraping.services.parse_pruning_service import clean_parsing_moderations, \
    unlink_website_from_parsing
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
                                                   source__exact='ml').all()
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

        # Parsings links
        self.info('Starting removing orphan parsing links')
        parsings = Parsing.objects.filter(website__isnull=False).all()
        counter = 0
        for parsing in parsings:
            if not parsing.prunings.filter(scrapings__page__website=parsing.website).exists() \
                    and not parsing.prunings.filter(images__website=parsing.website).exists():
                parsing.prunings.clear()
                unlink_website_from_parsing(parsing)
                counter += 1
        self.success(f'Done removing {counter} parsing links')

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
