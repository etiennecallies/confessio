from datetime import timedelta

from django.utils import timezone

from core.management.abstract_cleaning_command import AbstractCleaningCommand
from crawling.models import Log as CrawlingLog
from crawling.models import Scraping


class Command(AbstractCleaningCommand):
    help = "Clean crawling-related data from the database"

    def handle(self, *args, **options):
        self.clean_history(Scraping, Scraping.history.model)

        self.info('Starting removing old crawling logs')
        old_logs = CrawlingLog.objects.filter(
            created_at__lt=timezone.now() - timedelta(days=3)).all()
        counter = self.delete_objects(old_logs)
        self.success(f'Done removing {counter} old crawling logs')
