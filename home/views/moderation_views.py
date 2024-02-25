from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponseBadRequest
from django.shortcuts import render, redirect

from home.models import ParishModeration, ChurchModeration, ScrapingModeration


def get_moderate_response(request, category: str, resource: str,
                          class_moderation, moderation_uuid, render_moderation):
    if category not in class_moderation.Category.values:
        return HttpResponseBadRequest(f"category {category} is not valid for {resource}")

    if moderation_uuid is None:
        moderation = class_moderation.objects.filter(
            category=category, validated_at__isnull=True).first()
        if moderation is None:
            return redirect('index')
        else:
            return redirect(f'moderate_one_' + resource,
                            category=category,
                            moderation_uuid=moderation.uuid)

    try:
        moderation = class_moderation.objects.get(uuid=moderation_uuid)
    except class_moderation.DoesNotExist:
        print(f"{resource} {moderation_uuid} not found. "
              f"Probably because problem was solved meanwhile. "
              f"Redirecting to next moderation.")
        return redirect('moderate_next_' + resource, category=category)

    if request.method == "POST":
        moderation.validate(request.user)

        return redirect('moderate_next_' + resource, category=category)

    return render_moderation(request, moderation)


@login_required
@permission_required("home.change_sentence")
def moderate_parish(request, category, moderation_uuid=None):
    return get_moderate_response(request, category, 'parish', ParishModeration, moderation_uuid,
                                 render_parish_moderation)


def render_parish_moderation(request, moderation: ParishModeration):
    return render(request, f'pages/moderate_parish.html', {
        'parish_moderation': moderation,
        'parish': moderation.parish,
        'latest_crawling': moderation.parish.get_latest_crawling(),
    })


@login_required
@permission_required("home.change_sentence")
def moderate_church(request, category, moderation_uuid=None):
    return get_moderate_response(request, category, 'church', ChurchModeration, moderation_uuid,
                                 render_church_moderation)


def render_church_moderation(request, moderation: ChurchModeration):
    return render(request, f'pages/moderate_church.html', {
        'church_moderation': moderation,
        'church': moderation.church,
    })


@login_required
@permission_required("home.change_sentence")
def moderate_scraping(request, category, moderation_uuid=None):
    return get_moderate_response(request, category, 'scraping', ScrapingModeration, moderation_uuid,
                                 render_scraping_moderation)


def render_scraping_moderation(request, moderation: ScrapingModeration):
    return render(request, f'pages/moderate_scraping.html', {
        'scraping_moderation': moderation,
        'scraping': moderation.scraping,
    })
