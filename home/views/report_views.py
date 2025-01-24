from django.http import HttpResponseNotFound, HttpResponseBadRequest
from django.shortcuts import render

from home.models import Website
from home.models.report_models import Report
from home.services.events_service import get_website_merged_church_schedules_list
from home.services.page_url_service import get_page_pruning_urls


def report(request, website_uuid):
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

        report = Report(
            website=website,
            feedback_type=feedback_type,
            error_type=error_type,
            comment=comment
        )
        report.save()

        success_message = 'Merci pour votre retour !'

    website_churches = {}
    for parish in website.parishes.all():
        for church in parish.churches.all():
            website_churches.setdefault(website.uuid, []).append(church)

    # Get page url with #:~:text=
    page_pruning_urls = get_page_pruning_urls([website])

    website_merged_church_schedules_list = get_website_merged_church_schedules_list([website])

    return render(request, 'pages/report.html', {
        'noindex': True,
        'website': website,
        'website_churches': website_churches,
        'page_pruning_urls': page_pruning_urls,
        'website_merged_church_schedules_list': website_merged_church_schedules_list,
        'success_message': success_message,
    })
