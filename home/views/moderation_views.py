from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponseBadRequest
from django.shortcuts import render, redirect
from django.urls import reverse

from home.models import ParishModeration, ChurchModeration, ScrapingModeration, ModerationMixin
from scraping.utils.date_utils import datetime_to_ts_us, ts_us_to_datetime


def redirect_to_moderation(moderation: ModerationMixin, category: str, resource: str):
    if moderation is None:
        return redirect('index')
    else:
        return redirect(f'moderate_one_' + resource,
                        category=category,
                        moderation_uuid=moderation.uuid)


def get_moderate_response(request, category: str, resource: str,
                          class_moderation, moderation_uuid, render_moderation):
    if category not in class_moderation.Category.values:
        return HttpResponseBadRequest(f"category {category} is not valid for {resource}")

    if moderation_uuid is None:
        created_after_ts = int(request.GET.get('created_after', '0'))
        created_after = ts_us_to_datetime(created_after_ts)
        next_moderation = class_moderation.objects.filter(
            category=category, validated_at__isnull=True,
            created_at__gt=created_after) \
            .order_by('created_at').first()
        return redirect_to_moderation(next_moderation, category, resource)

    try:
        moderation = class_moderation.objects.get(uuid=moderation_uuid)
    except class_moderation.DoesNotExist:
        print(f"{resource} {moderation_uuid} not found. "
              f"Probably because problem was solved meanwhile. "
              f"Redirecting to first moderation.")
        return redirect('moderate_next_' + resource, category=category)

    created_at_ts_us = datetime_to_ts_us(moderation.created_at)
    next_url = reverse('moderate_next_' + resource,
                       kwargs={'category': category}) + f'?created_after={created_at_ts_us}'
    if request.method == "POST":
        moderation.validate(request.user)

        return redirect(next_url)

    return render_moderation(request, moderation, next_url)


@login_required
@permission_required("home.change_sentence")
def moderate_parish(request, category, moderation_uuid=None):
    return get_moderate_response(request, category, 'parish', ParishModeration, moderation_uuid,
                                 render_parish_moderation)


def render_parish_moderation(request, moderation: ParishModeration, next_url):
    return render(request, f'pages/moderate_parish.html', {
        'parish_moderation': moderation,
        'parish': moderation.parish,
        'latest_crawling': moderation.parish.get_latest_crawling(),
        'next_url': next_url,
    })


@login_required
@permission_required("home.change_sentence")
def moderate_church(request, category, moderation_uuid=None):
    return get_moderate_response(request, category, 'church', ChurchModeration, moderation_uuid,
                                 render_church_moderation)


def render_church_moderation(request, moderation: ChurchModeration, next_url):
    return render(request, f'pages/moderate_church.html', {
        'church_moderation': moderation,
        'church': moderation.church,
        'next_url': next_url,
    })


@login_required
@permission_required("home.change_sentence")
def moderate_scraping(request, category, moderation_uuid=None):
    return get_moderate_response(request, category, 'scraping', ScrapingModeration, moderation_uuid,
                                 render_scraping_moderation)


def render_scraping_moderation(request, moderation: ScrapingModeration, next_url):
    return render(request, f'pages/moderate_scraping.html', {
        'scraping_moderation': moderation,
        'scraping': moderation.scraping,
        'next_url': next_url,
    })
