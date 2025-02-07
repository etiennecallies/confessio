from home.models import ReportModeration, Website
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
    report_moderation = ReportModeration(report=report, category=category,
                                         diocese=report.website.get_diocese())
    report_moderation.save()


def get_count_and_label(website: Website):
    count_by_type = {}
    for report in website.reports.all():
        count_by_type[report.feedback_type] = count_by_type.get(report.feedback_type, 0) + 1

    count_and_label = []
    for feedback_type, label, singular_tooltip, plural_tooltip in [
        (Report.FeedbackType.GOOD, '👍', 'avis positif', 'avis positifs'),
        (Report.FeedbackType.OUTDATED, '👎', 'erreur signalée', 'erreurs signalées'),
        (Report.FeedbackType.ERROR, '❌', 'bug signalé', 'bugs signalés'),
        (Report.FeedbackType.COMMENT, '💬', 'commentaire', 'commentaires'),
    ]:
        if feedback_type in count_by_type:
            count = count_by_type[feedback_type]
            count_and_label.append({
                'count': count,
                'label': label,
                'tooltip': singular_tooltip if count <= 1 else plural_tooltip
            })

    return count_and_label
