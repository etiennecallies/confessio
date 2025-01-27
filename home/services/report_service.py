from home.models import ReportModeration
from home.models.report_models import Report


def get_report_moderation_category(report: Report) -> ReportModeration.Category:
    if report.feedback_type == Report.FeedbackType.GOOD:
        return ReportModeration.Category.GOOD
    elif report.feedback_type == Report.FeedbackType.OUTDATED:
        return ReportModeration.Category.OUTDATED
    elif report.feedback_type == Report.FeedbackType.ERROR:
        return ReportModeration.Category.ERROR


def add_necessary_moderation_for_report(report: Report):
    category = get_report_moderation_category(report)
    report_moderation = ReportModeration(report=report, category=category)
    report_moderation.save()
