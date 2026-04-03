from background_task.models import CompletedTask
from django.core.management import call_command

from core.management.abstract_cleaning_command import AbstractCleaningCommand


class Command(AbstractCleaningCommand):
    help = "Run all database cleaning tasks"

    def handle(self, *args, **options):
        call_command('clean_crawling')
        call_command('clean_scheduling')
        call_command('clean_registry')

        # Completed tasks (background tasks)
        self.info('Starting removing completed tasks')
        counter = self.delete_objects(CompletedTask.objects.all())
        self.success(f'Done removing {counter} completed tasks')
