import json

from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponseNotFound, HttpResponseBadRequest
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST

from crawling.models import CrawlingModeration
from front.views import get_moderate_response, redirect_to_moderation
from registry.models import Website
from registry.models.base_moderation_models import BUG_DESCRIPTION_MAX_LENGTH
from scheduling.models import ParsingModeration
from scheduling.models import SchedulingModeration, WebsiteSchedulesModeration
from scheduling.models.pruning_models import PruningModeration
from scheduling.models.pruning_models import SentenceModeration
from scheduling.services.merging.schedules_diff_service import validate_website_indexed_schedules
from scheduling.services.parsing.edit_parsing_service import set_llm_json_as_human_json
from scheduling.services.parsing.parsing_service import get_schedules_list_from_dict
from scheduling.services.pruning.edit_pruning_service import get_single_line_colored_piece, \
    TEMPORAL_COLORS, EVENT_MENTION_COLORS
from scheduling.services.pruning.edit_pruning_service import set_v2_indices_as_human
from scheduling.services.pruning.prune_scraping_service import SentenceQualifyLineInterface, \
    MLSentenceQualifyLineInterface
from scheduling.services.scheduling.scheduling_process_service import init_scheduling
from scheduling.services.scheduling.scheduling_service import get_parsing_moderation_of_pruning
from scheduling.workflows.pruning.extract.models import Source
from scheduling.workflows.pruning.extract_v2.split_content import create_line_and_tag_v2


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

    return render(request, f'moderations/moderate_pruning.html', {
        'moderation': moderation,
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

    return render(request, f'moderations/moderate_sentence.html', {
        'moderation': moderation,
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

    return render(request, f'moderations/moderate_parsing.html', {
        'moderation': moderation,
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
def moderate_scheduling(request, category, is_bug, diocese_slug, moderation_uuid=None):
    return get_moderate_response(request, category, 'scheduling', is_bug, diocese_slug,
                                 SchedulingModeration, moderation_uuid,
                                 render_scheduling_moderation)


def render_scheduling_moderation(request, moderation: SchedulingModeration, next_url):
    return render(request, f'moderations/moderate_scheduling.html', {
        'website': moderation.website,
        'moderation': moderation,
        'next_url': next_url,
        'bug_description_max_length': BUG_DESCRIPTION_MAX_LENGTH,
    })


@login_required
@permission_required("scheduling.change_sentence")
def moderate_website_schedules(request, category, is_bug, diocese_slug, moderation_uuid=None):
    return get_moderate_response(request, category, 'website_schedules', is_bug, diocese_slug,
                                 WebsiteSchedulesModeration, moderation_uuid,
                                 render_website_schedules_moderation)


def render_website_schedules_moderation(request, moderation: WebsiteSchedulesModeration, next_url):
    return render(request, 'moderations/moderate_website_schedules.html', {
        'website': moderation.website,
        'moderation': moderation,
        'next_url': next_url,
        'bug_description_max_length': BUG_DESCRIPTION_MAX_LENGTH,
    })


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


@login_required
@permission_required("scheduling.change_sentence")
@require_POST
def validate_schedules_for_website(request, website_uuid=None):
    try:
        website = Website.objects.get(uuid=website_uuid)
    except PruningModeration.DoesNotExist:
        return HttpResponseNotFound(f'website not found with uuid {website_uuid}')

    assert request.user is not None

    scheduling_moderation = SchedulingModeration.objects.get(website=website)
    if scheduling_moderation is not None:
        if scheduling_moderation.validated_at is None:
            scheduling_moderation.validate(request.user)
    crawling_moderation = CrawlingModeration.objects.get(website=website)
    if crawling_moderation is not None:
        if crawling_moderation.validated_at is None:
            crawling_moderation.validate(request.user)

    validate_website_indexed_schedules(website, request.user)
    init_scheduling(website)

    next_url = request.POST.get('next', '/')
    return redirect(next_url)
