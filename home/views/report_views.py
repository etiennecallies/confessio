import os

from django.http import HttpResponseNotFound, HttpResponseBadRequest
from django.shortcuts import render

from home.models import Website
from home.models.report_models import Report
from home.services.events_service import get_website_merged_church_schedules_list
from home.services.page_url_service import get_page_pruning_urls
from home.services.report_service import add_necessary_moderation_for_report
from home.utils.date_utils import get_current_day, get_current_year
from home.utils.hash_utils import hash_string_to_hex
from home.utils.web_utils import get_client_ip


def report_page(request, website_uuid):
    try:
        website = Website.objects.get(uuid=website_uuid)
    except Website.DoesNotExist:
        return HttpResponseNotFound(f'Website with uuid {website_uuid} not found')

    success_message = None
    if request.method == "POST":
        feedback_type_str = request.POST.get('feedback_type')
        error_type_str = request.POST.get('error_type')
        comment = request.POST.get('comment')

        if not feedback_type_str:
            return HttpResponseBadRequest('Feedback type is None')

        try:
            feedback_type = Report.FeedbackType(feedback_type_str)
        except ValueError:
            return HttpResponseBadRequest(f'Invalid feedback type: {feedback_type_str}')

        try:
            error_type = Report.ErrorType(error_type_str) if error_type_str else None
        except ValueError:
            return HttpResponseBadRequest(f'Invalid error type: {error_type_str}')

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

        success_message = 'Merci pour votre retour !'

    website_churches = {}
    for parish in website.parishes.all():
        for church in parish.churches.all():
            website_churches.setdefault(website.uuid, []).append(church)

    # Get page url with #:~:text=
    page_pruning_urls = get_page_pruning_urls([website])

    website_merged_church_schedules_list = get_website_merged_church_schedules_list(
        [website], website_churches)

    previous_reports = Report.objects.filter(website=website).order_by('-created_at').all()

    return render(request, 'pages/report.html', {
        'noindex': True,
        'website': website,
        'page_pruning_urls': page_pruning_urls,
        'website_merged_church_schedules_list': website_merged_church_schedules_list,
        'success_message': success_message,
        'previous_reports': previous_reports,
        'current_day': get_current_day(),
        'current_year': str(get_current_year()),
    })
