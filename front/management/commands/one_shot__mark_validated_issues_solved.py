from django.db.models import Max, Q

from core.management.abstract_command import AbstractCommand
from front.models import Issue
from registry.models.base_moderation_models import ModerationStatus


class Command(AbstractCommand):
    help = "Mark as solved the issues that already have a validated moderation."

    def handle(self, *args, **options):
        validated = Q(moderations__status=ModerationStatus.VALIDATED)
        issues = Issue.objects\
            .filter(validated, solved_at__isnull=True)\
            .annotate(validated_at=Max('moderations__updated_at', filter=validated))\
            .distinct()

        solved_count = 0
        for issue in issues:
            # Validation time is not stored, last update of the moderation is the closest we have
            issue.solved_at = issue.validated_at
            issue.save()
            solved_count += 1

        self.success(f'Marked {solved_count} issues as solved')
