from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponseNotFound, HttpResponseBadRequest

from core.views import get_moderate_response, ModerationPostError, redirect_to_moderation
from registry.models import WebsiteModeration, ChurchModeration, ParishModeration
from registry.models.base_moderation_models import ResourceDoesNotExistError, ModerationStatus
from registry.public_service import registry_merge_websites
from registry.services.church_human_service import on_church_human_validation
from registry.services.website_moderation_service import suggest_alternative_website
from crawling.models import Log as CrawlingLog


@login_required
@permission_required("scheduling.change_sentence")
def moderate_website(request, category, is_bug, diocese_slug, moderation_uuid=None):
    return get_moderate_response(request, category, 'website', is_bug, diocese_slug,
                                 WebsiteModeration, moderation_uuid,
                                 create_website_moderation_context,
                                 website_moderation_post_process)


def create_website_moderation_context(moderation: WebsiteModeration) -> dict:
    latest_crawling_log = moderation.website.crawling_logs.filter(
        type=CrawlingLog.Type.CRAWLING, status=CrawlingLog.Status.DONE
    ).order_by('-created_at').first()
    return {
        'website': moderation.website,
        'latest_crawling_log': latest_crawling_log,
    }


def website_moderation_post_process(request, moderation: WebsiteModeration) -> bool:
    if 'suggest_alternative_website' in request.POST:
        suggest_alternative_website(moderation)
        return False

    if 'replace_home_url' in request.POST:
        moderation.replace_home_url()

    return True


@login_required
@permission_required("scheduling.change_sentence")
def moderate_parish(request, category, is_bug, diocese_slug, moderation_uuid=None):
    return get_moderate_response(request, category, 'parish', is_bug, diocese_slug,
                                 ParishModeration, moderation_uuid,
                                 create_parish_moderation_context)


def create_parish_moderation_context(moderation: ParishModeration) -> dict:
    return {
        'parish': moderation.parish,
    }


def parish_moderation_post_process(request, moderation: ParishModeration) -> bool:
    if 'replace_name' in request.POST:
        moderation.replace_name()
    if 'replace_website' in request.POST:
        moderation.replace_website()
    if 'assign_external_id' in request.POST:
        similar_uuid = request.POST.get('assign_external_id')
        try:
            moderation.assign_external_id(similar_uuid)
        except ResourceDoesNotExistError:
            raise ModerationPostError(response=HttpResponseNotFound(
                f"church not found with uuid {similar_uuid}"))

    return True


@login_required
@permission_required("scheduling.change_sentence")
def moderate_church(request, category, is_bug, diocese_slug, moderation_uuid=None):
    return get_moderate_response(request, category, 'church', is_bug, diocese_slug,
                                 ChurchModeration, moderation_uuid,
                                 create_church_moderation_context)


def create_church_moderation_context(moderation: ChurchModeration) -> dict:
    return {
        'church': moderation.church,
        'similar_churches': moderation.get_similar_churches_sorted_by_name(),
    }


def church_moderation_post_process(request, moderation: ChurchModeration) -> bool:
    if 'replace_name' in request.POST:
        moderation.replace_name()
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
            raise ModerationPostError(response=HttpResponseNotFound(
                f"church not found with uuid {similar_uuid}"))

    on_church_human_validation(moderation)

    return True


@login_required
@permission_required("scheduling.change_sentence")
def moderate_merge_websites(request, website_moderation_uuid=None):
    try:
        website_moderation = WebsiteModeration.objects.get(uuid=website_moderation_uuid)
    except WebsiteModeration.DoesNotExist:
        return HttpResponseNotFound(f'website moderation not found with uuid '
                                    f'{website_moderation_uuid}')

    if website_moderation.other_website is None:
        return HttpResponseBadRequest(f'website moderation does not have other website')

    # other_website is the primary website
    registry_merge_websites(website_moderation.website, website_moderation.other_website)

    return redirect_to_moderation(website_moderation, website_moderation.category, 'website',
                                  website_moderation.status == ModerationStatus.BUG,
                                  website_moderation.get_diocese_slug())
