from django.http import HttpResponse, HttpResponseBadRequest

from front.models import Report, ReportModeration
from registry.models import Website
from core.services.admin_email_service import send_email_to_admin
from front.utils.web_utils import get_user_user_agent_and_ip


##############
# NEW REPORT #
##############

class NewReportError(Exception):
    response: HttpResponse


def new_report(request, website: Website) -> str:
    feedback_type_str = request.POST.get('feedback_type')
    error_type_str = request.POST.get('error_type')
    comment = request.POST.get('comment')
    main_report_uuid = request.POST.get('main_report_uuid')

    main_report = None
    if main_report_uuid is not None:
        try:
            main_report = Report.objects.get(uuid=main_report_uuid)
        except Report.DoesNotExist:
            raise NewReportError(HttpResponseBadRequest('Main report does not exist'))

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

    user, user_agent, ip_address_hash = get_user_user_agent_and_ip(request)

    report = Report(
        website=website,
        feedback_type=feedback_type,
        error_type=error_type,
        comment=comment,
        user_agent=user_agent,
        ip_address_hash=ip_address_hash,
        user=user,
        main_report=main_report,
    )
    report.save()

    if not user:
        add_necessary_moderation_for_report(report)

        email_body = (f"New report on website {website.name}\n"
                      f"feedback_type: {feedback_type}\n"
                      f"error_type: {error_type}\n\ncomment:\n{comment}")
        subject = f'New report on confessio for {website.name}'
        send_email_to_admin(subject, email_body)

    return 'Merci pour votre retour !'


def get_report_moderation_category(report: Report) -> ReportModeration.Category:
    if report.feedback_type == Report.FeedbackType.GOOD:
        return ReportModeration.Category.GOOD
    elif report.feedback_type == Report.FeedbackType.OUTDATED:
        return ReportModeration.Category.OUTDATED
    elif report.feedback_type == Report.FeedbackType.ERROR:
        return ReportModeration.Category.ERROR
    elif report.feedback_type == Report.FeedbackType.COMMENT:
        return ReportModeration.Category.COMMENT

    raise NotImplementedError


def add_necessary_moderation_for_report(report: Report):
    category = get_report_moderation_category(report)
    report_moderation = ReportModeration(report=report, category=category,
                                         diocese=report.website.get_diocese())
    report_moderation.save()


####################
# PREVIOUS REPORTS #
####################

def get_previous_reports(website: Website) -> list[list[Report]]:
    all_reports = list(Report.objects.filter(website=website).order_by('created_at').all())

    main_reports = []
    reports_by_main_report = {}
    for report in all_reports:
        if report.main_report:
            reports_by_main_report[report.main_report.uuid].append(report)
        else:
            main_reports.append(report)
            reports_by_main_report[report.uuid] = [report]

    return [reports_by_main_report[main_report.uuid] for main_report in reversed(main_reports)]


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
