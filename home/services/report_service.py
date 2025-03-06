import os

from django.http import HttpResponse, HttpResponseBadRequest

from home.models import ReportModeration, Website
from home.models.report_models import Report
from home.utils.hash_utils import hash_string_to_hex
from home.utils.web_utils import get_client_ip


##############
# NEW REPORT #
##############

class NewReportError(Exception):
    response: HttpResponse


def new_report(request, website: Website) -> str:
    feedback_type_str = request.POST.get('feedback_type')
    error_type_str = request.POST.get('error_type')
    comment = request.POST.get('comment')

    if not feedback_type_str:
        raise NewReportError(HttpResponseBadRequest('Feedback type is None'))

    try:
        feedback_type = Report.FeedbackType(feedback_type_str)
    except ValueError:
        raise NewReportError(HttpResponseBadRequest(
            f'Invalid feedback type: {feedback_type_str}'))

    try:
        error_type = Report.ErrorType(error_type_str) if error_type_str else None
    except ValueError:
        raise NewReportError(HttpResponseBadRequest(f'Invalid error type: {error_type_str}'))

    user_agent = request.META['HTTP_USER_AGENT']
    ip_hash_salt = os.environ.get('IP_HASH_SALT')
    ip_address_hash = hash_string_to_hex(ip_hash_salt + get_client_ip(request))

    user = request.user if request.user.is_authenticated else None

    report = Report(
        website=website,
        feedback_type=feedback_type,
        error_type=error_type,
        comment=comment,
        user_agent=user_agent,
        ip_address_hash=ip_address_hash,
        user=user,
    )
    report.save()
    add_necessary_moderation_for_report(report)

    return 'Merci pour votre retour !'


def get_report_moderation_category(report: Report) -> ReportModeration.Category:
    if report.feedback_type == Report.FeedbackType.GOOD:
        return ReportModeration.Category.GOOD
    elif report.feedback_type == Report.FeedbackType.OUTDATED:
        return ReportModeration.Category.OUTDATED
    elif report.feedback_type == Report.FeedbackType.ERROR:
        return ReportModeration.Category.ERROR

    raise NotImplementedError


def add_necessary_moderation_for_report(report: Report):
    category = get_report_moderation_category(report)
    report_moderation = ReportModeration(report=report, category=category,
                                         diocese=report.website.get_diocese())
    report_moderation.save()


####################
# PREVIOUS REPORTS #
####################

def get_previous_reports(website: Website) -> list[Report]:
    return list(Report.objects.filter(website=website).order_by('-created_at').all())


##################
# COUNT & LABELS #
##################

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
