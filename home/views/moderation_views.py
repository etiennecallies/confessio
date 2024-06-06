from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponseBadRequest, HttpResponseNotFound
from django.shortcuts import render, redirect
from django.urls import reverse

from home.models import WebsiteModeration, ChurchModeration, ScrapingModeration, ModerationMixin, \
    BUG_DESCRIPTION_MAX_LENGTH, ParishModeration
from scraping.services.merge_websites_service import merge_websites
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
            if 'replace_name' in request.POST:
                moderation.replace_name()
            if 'replace_location' in request.POST:
                moderation.replace_location()
            moderation.validate(request.user)

        return redirect(next_url)

    return render_moderation(request, moderation, next_url)


@login_required
@permission_required("home.change_sentence")
def moderate_website(request, category, is_bug, moderation_uuid=None):
    return get_moderate_response(request, category, 'website', is_bug, WebsiteModeration,
                                 moderation_uuid, render_website_moderation)


def render_website_moderation(request, moderation: WebsiteModeration, next_url):
    return render(request, f'pages/moderate_website.html', {
        'website_moderation': moderation,
        'website': moderation.website,
        'latest_crawling': moderation.website.get_latest_crawling(),
        'next_url': next_url,
        'bug_description_max_length': BUG_DESCRIPTION_MAX_LENGTH,
    })


@login_required
@permission_required("home.change_sentence")
def moderate_parish(request, category, is_bug, moderation_uuid=None):
    return get_moderate_response(request, category, 'parish', is_bug, ParishModeration,
                                 moderation_uuid, render_parish_moderation)


def render_parish_moderation(request, moderation: ParishModeration, next_url):
    return render(request, f'pages/moderate_parish.html', {
        'parish_moderation': moderation,
        'parish': moderation.parish,
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
def moderate_merge_websites(request, website_moderation_uuid=None):
    try:
        website_moderation = WebsiteModeration.objects.get(uuid=website_moderation_uuid)
    except WebsiteModeration.DoesNotExist:
        return HttpResponseNotFound(f'website moderation not found with uuid {website_moderation_uuid}')

    if website_moderation.other_website is None:
        return HttpResponseBadRequest(f'website moderation does not have other website')

    # other_website is the primary website
    merge_websites(website_moderation.website, website_moderation.other_website)

    return redirect_to_moderation(website_moderation, website_moderation.category, 'website',
                                  website_moderation.marked_as_bug_at is not None)
