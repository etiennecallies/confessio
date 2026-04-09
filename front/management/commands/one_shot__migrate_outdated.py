from core.management.abstract_command import AbstractCommand
from front.models import Report, ReportModeration


class Command(AbstractCommand):
    help = "One shot command to migrate outdated report"

    def handle(self, *args, **options):
        self.info(f'Starting migration')
        reports = Report.objects.filter(feedback_type=Report.FeedbackType.OUTDATED).all()
        count = 0
        for report in reports:
            report.feedback_type = Report.FeedbackType.ERROR
            report.error_type = Report.ErrorType.OUTDATED
            report.save()
            count += 1
        self.success(f'Finished migration for {count} reports')

        self.info(f'Starting migration for moderation')
        report_moderations = ReportModeration.objects\
            .filter(category=ReportModeration.Category.OUTDATED).all()
        count = 0
        for report_moderation in report_moderations:
            report_moderation.category = ReportModeration.Category.ERROR
            report_moderation.save()
            count += 1
        self.success(f'Finished migration for moderation for {count} reports')
