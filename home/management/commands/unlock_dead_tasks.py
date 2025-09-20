from datetime import timedelta

from background_task.models import Task
from django.utils import timezone

from core.settings import MAX_RUN_TIME
from home.management.abstract_command import AbstractCommand


class Command(AbstractCommand):
    help = "Unlock dead tasks that are locked for more than 5 minutes"

    def handle(self, *args, **options):
        self.info(f'Starting unlocking dead tasks...')
        # This is a bug in django-background-tasks that does not unlock tasks that crashed
        # after MAX_RUN_TIME seconds
        Task.objects.filter(locked_at__lte=timezone.now() - timedelta(seconds=MAX_RUN_TIME))\
            .update(locked_at=None, locked_by=None)
        self.success(f'Finished unlocking dead tasks')
