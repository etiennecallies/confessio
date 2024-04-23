from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponseBadRequest, HttpResponseNotFound
from django.shortcuts import render, redirect
from django.urls import reverse

from home.models import ParishModeration, ChurchModeration, ScrapingModeration, ModerationMixin, \
    BUG_DESCRIPTION_MAX_LENGTH
from scraping.services.merge_parishes_service import merge_parishes
from scraping.utils.date_utils import datetime_to_ts_us, ts_us_to_datetime


def redirect_to_moderation(moderation: ModerationMixin, category: str, resource: str, is_bug: bool):
    if moderation is None:
        return redirect('index')
    else:
        return redirect(f'moderate_one_' + resource,
                        category=category,
                        is_bug=is_bug,
                        moderation_uuid=moderation.uuid)


def get_moderate_response(request, category: str, resource: str, is_bug_as_str: bool,
                          class_moderation, moderation_uuid, render_moderation):
    if is_bug_as_str not in ['True', 'False']:
        return HttpResponseBadRequest(f"is_bug_as_str {is_bug_as_str} is not valid")

    is_bug = is_bug_as_str == 'True'

    if category not in class_moderation.Category.values:
        return HttpResponseBadRequest(f"category {category} is not valid for {resource}")

    if moderation_uuid is None:
        created_after_ts = int(request.GET.get('created_after', '0'))
        created_after = ts_us_to_datetime(created_after_ts)
        next_moderation = class_moderation.objects.filter(
            category=category, validated_at__isnull=True, marked_as_bug_at__isnull=not is_bug,
            created_at__gt=created_after) \
            .order_by('created_at').first()
        return redirect_to_moderation(next_moderation, category, resource, is_bug)

    try:
        moderation = class_moderation.objects.get(uuid=moderation_uuid)
    except class_moderation.DoesNotExist:
        print(f"{resource} {moderation_uuid} not found. "
              f"Probably because problem was solved meanwhile. "
              f"Redirecting to first moderation.")
        return redirect('moderate_next_' + resource, category=category, is_bug=is_bug)

    created_at_ts_us = datetime_to_ts_us(moderation.created_at)
    next_url = \
        reverse('moderate_next_' + resource, kwargs={'category': category, 'is_bug': is_bug}) \
        + f'?created_after={created_at_ts_us}'
    if request.method == "POST":
        if 'bug_description' in request.POST:
            bug_description = request.POST.get('bug_description')
            if bug_description is not None and len(bug_description) > BUG_DESCRIPTION_MAX_LENGTH:
                return HttpResponseBadRequest(f"bug_description is len {len(bug_description)} but "
                                              f"max size is {BUG_DESCRIPTION_MAX_LENGTH}")
            moderation.mark_as_bug(request.user, bug_description)
        else:
            moderation.validate(request.user)

        return redirect(next_url)

    return render_moderation(request, moderation, next_url)


@login_required
@permission_required("home.change_sentence")
def moderate_parish(request, category, is_bug, moderation_uuid=None):
    return get_moderate_response(request, category, 'parish', is_bug, ParishModeration,
                                 moderation_uuid, render_parish_moderation)


def render_parish_moderation(request, moderation: ParishModeration, next_url):
    return render(request, f'pages/moderate_parish.html', {
        'parish_moderation': moderation,
        'parish': moderation.parish,
        'latest_crawling': moderation.parish.get_latest_crawling(),
        'next_url': next_url,
        'bug_description_max_length': BUG_DESCRIPTION_MAX_LENGTH,
    })


@login_required
@permission_required("home.change_sentence")
def moderate_church(request, category, is_bug, moderation_uuid=None):
    return get_moderate_response(request, category, 'church', is_bug, ChurchModeration,
                                 moderation_uuid, render_church_moderation)


def render_church_moderation(request, moderation: ChurchModeration, next_url):
    return render(request, f'pages/moderate_church.html', {
        'church_moderation': moderation,
        'church': moderation.church,
        'next_url': next_url,
        'bug_description_max_length': BUG_DESCRIPTION_MAX_LENGTH,
    })


@login_required
@permission_required("home.change_sentence")
def moderate_scraping(request, category, is_bug, moderation_uuid=None):
    return get_moderate_response(request, category, 'scraping', is_bug, ScrapingModeration,
                                 moderation_uuid, render_scraping_moderation)


def render_scraping_moderation(request, moderation: ScrapingModeration, next_url):
    assert moderation.scraping is not None

    return render(request, f'pages/moderate_scraping.html', {
        'scraping_moderation': moderation,
        'scraping': moderation.scraping,
        'next_url': next_url,
        'bug_description_max_length': BUG_DESCRIPTION_MAX_LENGTH,
    })


@login_required
@permission_required("home.change_sentence")
def moderate_merge_parishes(request, parish_moderation_uuid=None):
    try:
        parish_moderation = ParishModeration.objects.get(uuid=parish_moderation_uuid)
    except ParishModeration.DoesNotExist:
        return HttpResponseNotFound(f'parish moderation not found with uuid {parish_moderation_uuid}')

    if parish_moderation.other_parish is None:
        return HttpResponseBadRequest(f'parish moderation does not have other parish')

    # other_parish is the primary parish
    merge_parishes(parish_moderation.website, parish_moderation.other_parish)

    return redirect_to_moderation(parish_moderation, parish_moderation.category, 'parish',
                                  parish_moderation.marked_as_bug_at is not None)
