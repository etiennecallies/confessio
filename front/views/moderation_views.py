import json

from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponseBadRequest, HttpResponseNotFound
from django.shortcuts import render, redirect
from django.urls import reverse

from fetching.models import OClocherOrganizationModeration, OClocherMatchingModeration
from front.models import ReportModeration
from registry.models import WebsiteModeration, ChurchModeration, ModerationMixin, \
    ParishModeration, Diocese
from registry.models.base_moderation_models import BUG_DESCRIPTION_MAX_LENGTH, \
    ResourceDoesNotExistError
from registry.public_service import registry_suggest_alternative_website
from registry.services.church_human_service import on_church_human_validation
from registry.services.merge_websites_service import merge_websites
from scheduling.models.parsing_models import ParsingModeration
from scheduling.models.pruning_models import PruningModeration, SentenceModeration
from scheduling.services.edit_parsing_service import on_parsing_human_validation, \
    ParsingValidationError, set_llm_json_as_human_json
from scheduling.services.edit_pruning_service import on_pruning_human_validation, \
    set_v2_indices_as_human, get_single_line_colored_piece, update_sentence_labels_with_request, \
    TEMPORAL_COLORS, EVENT_MENTION_COLORS
from scheduling.services.parsing_service import get_schedules_list_from_dict
from scheduling.services.prune_scraping_service import SentenceQualifyLineInterface, \
    MLSentenceQualifyLineInterface
from scheduling.services.reparse_parsing_service import reparse_parsing
from scheduling.services.scheduling_service import get_parsing_moderation_of_pruning
from scheduling.utils.date_utils import datetime_to_ts_us, ts_us_to_datetime
from scheduling.workflows.pruning.extract_v2.split_content import create_line_and_tag_v2
from scheduling.workflows.pruning.models import Source


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
                on_church_human_validation(moderation)

            moderation.validate(request.user)

        if do_redirect:
            return redirect(next_url)

    return render_moderation(request, moderation, next_url)


@login_required
@permission_required("scheduling.change_sentence")
def moderate_website(request, category, is_bug, diocese_slug, moderation_uuid=None):
    return get_moderate_response(request, category, 'website', is_bug, diocese_slug,
                                 WebsiteModeration, moderation_uuid, render_website_moderation)


def render_website_moderation(request, moderation: WebsiteModeration, next_url):
    return render(request, f'pages/moderate_website.html', {
        'website_moderation': moderation,
        'website': moderation.website,
        'latest_crawling': moderation.website.crawling,
        'next_url': next_url,
        'bug_description_max_length': BUG_DESCRIPTION_MAX_LENGTH,
    })


@login_required
@permission_required("scheduling.change_sentence")
def moderate_parish(request, category, is_bug, diocese_slug, moderation_uuid=None):
    return get_moderate_response(request, category, 'parish', is_bug, diocese_slug,
                                 ParishModeration, moderation_uuid, render_parish_moderation)


def render_parish_moderation(request, moderation: ParishModeration, next_url):
    return render(request, f'pages/moderate_parish.html', {
        'parish_moderation': moderation,
        'parish': moderation.parish,
        'next_url': next_url,
        'bug_description_max_length': BUG_DESCRIPTION_MAX_LENGTH,
    })


@login_required
@permission_required("scheduling.change_sentence")
def moderate_church(request, category, is_bug, diocese_slug, moderation_uuid=None):
    return get_moderate_response(request, category, 'church', is_bug, diocese_slug,
                                 ChurchModeration, moderation_uuid, render_church_moderation)


def render_church_moderation(request, moderation: ChurchModeration, next_url):
    return render(request, f'pages/moderate_church.html', {
        'church_moderation': moderation,
        'church': moderation.church,
        'similar_churches': moderation.get_similar_churches_sorted_by_name(),
        'next_url': next_url,
        'bug_description_max_length': BUG_DESCRIPTION_MAX_LENGTH,
    })


@login_required
@permission_required("scheduling.change_sentence")
def moderate_pruning(request, category, is_bug, diocese_slug, moderation_uuid=None):
    return get_moderate_response(request, category, 'pruning', is_bug, diocese_slug,
                                 PruningModeration, moderation_uuid, render_pruning_moderation)


def render_pruning_moderation(request, moderation: PruningModeration, next_url):
    pruning = moderation.pruning
    assert pruning is not None

    differs_by_index = []
    for i in range(len(pruning.extracted_html.split('<br>\n'))):
        i_in_ml = None if pruning.ml_indices is None else i in pruning.ml_indices
        i_in_human = None if pruning.human_indices is None else i in pruning.human_indices
        i_in_v2 = None if pruning.v2_indices is None else i in pruning.v2_indices

        values = list(filter(lambda b: b is not None, [i_in_ml, i_in_human, i_in_v2]))
        differs_by_index.append(len(set(values)) > 1)

    ml_lines_and_colors = []
    for i, line in enumerate(pruning.extracted_html.split('<br>\n')):
        color = '' if i in (pruning.ml_indices or []) else 'text-warning'
        differs = 'fw-bold display-5' if differs_by_index[i] else ''
        ml_lines_and_colors.append((line, color, differs))

    human_lines_and_colors = []
    if pruning.human_indices is not None:
        for i, line in enumerate(pruning.extracted_html.split('<br>\n')):
            color = '' if i in pruning.human_indices else 'text-warning'
            differs = 'fw-bold display-5' if differs_by_index[i] else ''
            human_lines_and_colors.append((line, color, differs))

    v2_lines_and_colors = []
    if pruning.v2_indices is not None:
        for i, line in enumerate(pruning.extracted_html.split('<br>\n')):
            color = '' if i in pruning.v2_indices else 'text-warning'
            differs = 'fw-bold display-5' if differs_by_index[i] else ''
            v2_lines_and_colors.append((line, color, differs))

    parsing_moderation = get_parsing_moderation_of_pruning(pruning)

    return render(request, f'pages/moderate_pruning.html', {
        'pruning_moderation': moderation,
        'pruning': pruning,
        'next_url': next_url,
        'bug_description_max_length': BUG_DESCRIPTION_MAX_LENGTH,
        'ml_lines_and_colors': ml_lines_and_colors,
        'human_lines_and_colors': human_lines_and_colors,
        'v2_lines_and_colors': v2_lines_and_colors,
        'parsing_moderation': parsing_moderation,
    })


@login_required
@permission_required("scheduling.change_sentence")
def moderate_sentence(request, category, is_bug, diocese_slug, moderation_uuid=None):
    return get_moderate_response(request, category, 'sentence', is_bug, diocese_slug,
                                 SentenceModeration, moderation_uuid, render_sentence_moderation)


def render_sentence_moderation(request, moderation: SentenceModeration, next_url):
    assert moderation.sentence is not None

    line_and_tag_human = create_line_and_tag_v2(moderation.sentence.line,
                                                SentenceQualifyLineInterface())
    colored_piece_human = get_single_line_colored_piece(
        line_and_tag_human, Source.HUMAN, i=1, do_show=True)
    line_and_tag_ml = create_line_and_tag_v2(moderation.sentence.line,
                                             MLSentenceQualifyLineInterface())
    colored_piece_ml = get_single_line_colored_piece(
        line_and_tag_ml, Source.ML, i=2, do_show=True)

    return render(request, f'pages/moderate_sentence.html', {
        'sentence_moderation': moderation,
        'sentence': moderation.sentence,
        'colored_pieces': [colored_piece_human, colored_piece_ml],
        'temporal_colors': TEMPORAL_COLORS,
        'event_mention_colors': EVENT_MENTION_COLORS,
        'next_url': next_url,
        'bug_description_max_length': BUG_DESCRIPTION_MAX_LENGTH,
    })


@login_required
@permission_required("scheduling.change_sentence")
def moderate_parsing(request, category, is_bug, diocese_slug, moderation_uuid=None):
    return get_moderate_response(request, category, 'parsing', is_bug, diocese_slug,
                                 ParsingModeration, moderation_uuid, render_parsing_moderation)


def render_parsing_moderation(request, moderation: ParsingModeration, next_url):
    parsing = moderation.parsing
    assert parsing is not None

    truncated_html = parsing.truncated_html
    if parsing.llm_json:
        llm_schedules_list = get_schedules_list_from_dict(parsing.llm_json,
                                                          parsing.llm_json_version)
    else:
        llm_schedules_list = None

    if parsing.human_json:
        human_schedules_list = get_schedules_list_from_dict(parsing.human_json,
                                                            parsing.human_json_version)
    else:
        human_schedules_list = None

    church_desc_by_id_json = json.dumps(parsing.church_desc_by_id, indent=2, ensure_ascii=False)
    back_path = request.GET.get('backPath', '')

    return render(request, f'pages/moderate_parsing.html', {
        'parsing_moderation': moderation,
        'parsing': parsing,
        'church_desc_by_id_json': church_desc_by_id_json,
        'truncated_html': truncated_html,
        'llm_schedules_list': llm_schedules_list,
        'human_schedules_list': human_schedules_list,
        'next_url': next_url,
        'bug_description_max_length': BUG_DESCRIPTION_MAX_LENGTH,
        'back_path': back_path,
    })


@login_required
@permission_required("scheduling.change_sentence")
def moderate_report(request, category, is_bug, diocese_slug, moderation_uuid=None):
    return get_moderate_response(request, category, 'report', is_bug, diocese_slug,
                                 ReportModeration, moderation_uuid, render_report_moderation)


def render_report_moderation(request, moderation: ReportModeration, next_url):
    report = moderation.report
    assert report is not None

    return render(request, f'pages/moderate_report.html', {
        'report': report,
        'report_moderation': moderation,
        'next_url': next_url,
        'bug_description_max_length': BUG_DESCRIPTION_MAX_LENGTH,
    })


@login_required
@permission_required("scheduling.change_sentence")
def moderate_oclocher_organization(request, category, is_bug, diocese_slug, moderation_uuid=None):
    return get_moderate_response(request, category, 'oclocher_organization', is_bug, diocese_slug,
                                 OClocherOrganizationModeration,
                                 moderation_uuid, render_oclocher_organization_moderation)


def render_oclocher_organization_moderation(request, moderation: OClocherOrganizationModeration,
                                            next_url):
    oclocher_organization = moderation.oclocher_organization
    assert oclocher_organization is not None

    return render(request, f'pages/moderate_oclocher_organization.html', {
        'oclocher_organization': oclocher_organization,
        'moderation': moderation,
        'next_url': next_url,
        'bug_description_max_length': BUG_DESCRIPTION_MAX_LENGTH,
    })


@login_required
@permission_required("scheduling.change_sentence")
def moderate_oclocher_matching(request, category, is_bug, diocese_slug, moderation_uuid=None):
    return get_moderate_response(request, category, 'oclocher_matching', is_bug, diocese_slug,
                                 OClocherMatchingModeration,
                                 moderation_uuid, render_oclocher_matching_moderation)


def render_oclocher_matching_moderation(request, moderation: OClocherMatchingModeration,
                                        next_url):
    oclocher_matching = moderation.oclocher_matching
    assert oclocher_matching is not None

    return render(request, f'pages/moderate_oclocher_matching.html', {
        'oclocher_matching': oclocher_matching,
        'moderation': moderation,
        'next_url': next_url,
        'bug_description_max_length': BUG_DESCRIPTION_MAX_LENGTH,
    })


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
    merge_websites(website_moderation.website, website_moderation.other_website)

    return redirect_to_moderation(website_moderation, website_moderation.category, 'website',
                                  website_moderation.marked_as_bug_at is not None,
                                  website_moderation.get_diocese_slug())


@login_required
@permission_required("scheduling.change_sentence")
def moderate_erase_human_by_llm(request, parsing_moderation_uuid=None):
    try:
        parsing_moderation = ParsingModeration.objects.get(uuid=parsing_moderation_uuid)
    except ParsingModeration.DoesNotExist:
        return HttpResponseNotFound(f'parsing moderation not found with uuid '
                                    f'{parsing_moderation_uuid}')

    parsing = parsing_moderation.parsing
    if parsing.llm_json is None:
        return HttpResponseBadRequest(f'Can not erase human by llm because parsing '
                                      f'{parsing.uuid} does not have llm_json')

    set_llm_json_as_human_json(parsing)

    return redirect_to_moderation(parsing_moderation, parsing_moderation.category, 'parsing',
                                  parsing_moderation.marked_as_bug_at is not None,
                                  parsing_moderation.get_diocese_slug())


@login_required
@permission_required("scheduling.change_sentence")
def moderate_set_v2_indices_as_human_by(request, pruning_moderation_uuid=None):
    try:
        pruning_moderation = PruningModeration.objects.get(uuid=pruning_moderation_uuid)
    except PruningModeration.DoesNotExist:
        return HttpResponseNotFound(f'pruning moderation not found with uuid '
                                    f'{pruning_moderation_uuid}')

    pruning = pruning_moderation.pruning
    if pruning.v2_indices is None:
        return HttpResponseBadRequest(f'Can not erase human by llm because parsing '
                                      f'{pruning.uuid} does not have llm_json')

    set_v2_indices_as_human(pruning)

    return redirect_to_moderation(pruning_moderation, pruning_moderation.category, 'pruning',
                                  pruning_moderation.marked_as_bug_at is not None,
                                  pruning_moderation.get_diocese_slug())
