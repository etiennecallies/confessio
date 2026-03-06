from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponseBadRequest, HttpResponseNotFound
from django.shortcuts import render, redirect
from django.urls import reverse

from front.models import ReportModeration
from registry.models import ChurchModeration, ModerationMixin, Diocese
from registry.models.base_moderation_models import BUG_DESCRIPTION_MAX_LENGTH, \
    ResourceDoesNotExistError
from registry.public_service import registry_suggest_alternative_website, \
    registry_on_church_human_validation
from scheduling.models import ParsingModeration
from scheduling.models.pruning_models import PruningModeration
from scheduling.services.parsing.edit_parsing_service import on_parsing_human_validation, \
    ParsingValidationError
from scheduling.services.parsing.reparse_parsing_service import reparse_parsing
from scheduling.services.pruning.edit_pruning_service import on_pruning_human_validation, \
    update_sentence_labels_with_request
from scheduling.utils.date_utils import datetime_to_ts_us, ts_us_to_datetime


def redirect_to_moderation(moderation: ModerationMixin, category: str, resource: str, is_bug: bool,
                           diocese_slug: str):
    if moderation is None:
        return redirect('index')
    else:
        return redirect(f'moderate_one_' + resource,
                        category=category,
                        is_bug=is_bug,
                        moderation_uuid=moderation.uuid,
                        diocese_slug=diocese_slug)


def get_moderate_response(request, category: str, resource: str, is_bug_as_str: bool,
                          diocese_slug: str, class_moderation, moderation_uuid, render_moderation):
    if is_bug_as_str not in ['True', 'False']:
        return HttpResponseBadRequest(f"is_bug_as_str {is_bug_as_str} is not valid")

    is_bug = is_bug_as_str == 'True'

    if category not in class_moderation.Category.values:
        return HttpResponseBadRequest(f"category {category} is not valid for {resource}")

    if diocese_slug == 'no_diocese':
        diocese = None
    else:
        try:
            diocese = Diocese.objects.get(slug=diocese_slug)
        except Diocese.DoesNotExist:
            return HttpResponseNotFound(f"diocese {diocese_slug} not found")

    if moderation_uuid is None:
        created_after_ts = int(request.GET.get('created_after', '0'))
        created_after = ts_us_to_datetime(created_after_ts)
        objects_filter = class_moderation.objects.filter(category=category,
                                                         validated_at__isnull=True,
                                                         marked_as_bug_at__isnull=not is_bug,
                                                         created_at__gt=created_after)
        if diocese:
            objects_filter = objects_filter.filter(diocese=diocese)
        next_moderation = objects_filter.order_by('created_at').first()
        return redirect_to_moderation(next_moderation, category, resource, is_bug, diocese_slug)

    try:
        moderation = class_moderation.objects.get(uuid=moderation_uuid)
    except class_moderation.DoesNotExist:
        print(f"{resource} {moderation_uuid} not found. "
              f"Probably because problem was solved meanwhile. "
              f"Redirecting to first moderation.")
        return redirect('moderate_next_' + resource, category=category, is_bug=is_bug,
                        diocese_slug=diocese_slug)

    created_at_ts_us = datetime_to_ts_us(moderation.created_at)
    back_path = request.GET.get('backPath', '')
    if back_path:
        next_url = back_path
    else:
        next_url = \
            reverse('moderate_next_' + resource,
                    kwargs={'category': category, 'is_bug': is_bug, 'diocese_slug': diocese_slug}) \
            + f'?created_after={created_at_ts_us}'
    related_url = request.POST.get('related_url')
    if related_url:
        next_url = f"{related_url}?backPath={next_url}"

    do_redirect = True
    if request.method == "POST":
        if 'bug_description' in request.POST:
            bug_description = request.POST.get('bug_description')
            if bug_description is not None and len(bug_description) > BUG_DESCRIPTION_MAX_LENGTH:
                return HttpResponseBadRequest(f"bug_description is len {len(bug_description)} but "
                                              f"max size is {BUG_DESCRIPTION_MAX_LENGTH}")
            moderation.mark_as_bug(request.user, bug_description)
        elif 'delete_moderation' in request.POST:
            moderation.delete()
        elif 'reparse_parsing' in request.POST:
            reparse_parsing(moderation.parsing)
            do_redirect = False
        elif 'suggest_alternative_website' in request.POST:
            registry_suggest_alternative_website(moderation)
            do_redirect = False
        elif 'update_human_labels' in request.POST:
            update_sentence_labels_with_request(request, "1", moderation.sentence, None)
            do_redirect = False
        else:
            if 'replace_home_url' in request.POST:
                moderation.replace_home_url()
            if 'replace_name' in request.POST:
                moderation.replace_name()
            if 'replace_website' in request.POST:
                moderation.replace_website()
            if 'replace_parish' in request.POST:
                moderation.replace_parish()
            if 'replace_location' in request.POST:
                moderation.replace_location()
            if 'replace_address' in request.POST:
                moderation.replace_address()
            if 'replace_zipcode' in request.POST:
                moderation.replace_zipcode()
            if 'replace_city' in request.POST:
                moderation.replace_city()
            if 'replace_messesinfo_id' in request.POST:
                moderation.replace_messesinfo_id()
            if 'assign_external_id' in request.POST:
                similar_uuid = request.POST.get('assign_external_id')
                try:
                    moderation.assign_external_id(similar_uuid)
                except ResourceDoesNotExistError:
                    return HttpResponseNotFound(
                        f"resource {resource} not found with uuid {similar_uuid}")

            if class_moderation == PruningModeration:
                on_pruning_human_validation(moderation.pruning)
            elif class_moderation == ParsingModeration:
                try:
                    on_parsing_human_validation(moderation)
                except ParsingValidationError as e:
                    return HttpResponseBadRequest(str(e))
            elif class_moderation == ChurchModeration:
                registry_on_church_human_validation(moderation)

            moderation.validate(request.user)

        if do_redirect:
            return redirect(next_url)

    return render_moderation(request, moderation, next_url)


@login_required
@permission_required("scheduling.change_sentence")
def moderate_report(request, category, is_bug, diocese_slug, moderation_uuid=None):
    return get_moderate_response(request, category, 'report', is_bug, diocese_slug,
                                 ReportModeration, moderation_uuid, render_report_moderation)


def render_report_moderation(request, moderation: ReportModeration, next_url):
    report = moderation.report
    assert report is not None

    return render(request, f'moderations/moderate_report.html', {
        'report': report,
        'report_moderation': moderation,
        'next_url': next_url,
        'bug_description_max_length': BUG_DESCRIPTION_MAX_LENGTH,
    })
