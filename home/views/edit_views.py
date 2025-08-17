import json

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponseNotFound
from django.shortcuts import render
from pydantic import ValidationError

from home.models import Page, Pruning, Sentence, Parsing
from home.services.edit_pruning_service import get_colored_pieces, update_sentence_action, \
    reset_pages_counter_of_pruning, set_ml_indices_as_human, set_human_indices, \
    get_pruning_human_pieces, get_colored_pieces_v2, set_v2_indices_as_human
from jsoneditor.forms import JSONSchemaForm
from scraping.extract_v2.models import EventMotion
from scraping.extract_v2.qualify_line_interfaces import DummyQualifyLineInterface
from scraping.parse.schedules import SchedulesList
from scraping.prune.action_interfaces import DummyActionInterface
from scraping.prune.models import Action
from scraping.services.parse_pruning_service import reset_counters_of_parsing, \
    re_index_related_website
from scraping.services.parsing_service import get_parsing_schedules_list
from scraping.services.prune_scraping_service import SentenceFromDbActionInterface, \
    reprune_affected_prunings, prune_pruning, SentenceQualifyLineInterface
from scraping.utils.html_utils import split_lines


@login_required
@permission_required("home.change_sentence")
def edit_pruning_v1(request, pruning_uuid):
    try:
        pruning = Pruning.objects.get(uuid=pruning_uuid)
    except Page.DoesNotExist:
        return HttpResponseNotFound("Pruning not found")

    extracted_html = pruning.extracted_html

    if request.method == "POST":
        # We extract action per line from POST
        dummy_colored_pieces = get_colored_pieces(extracted_html,
                                                  DummyActionInterface())
        modified_sentences = []
        for dummy_piece in dummy_colored_pieces:
            new_action = Action(request.POST.get(f"action-{dummy_piece.id}"))
            sentence_uuid = request.POST.get(f"sentence-uuid-{dummy_piece.id}")
            sentence = Sentence.objects.get(uuid=sentence_uuid)

            if Action(sentence.action) != new_action:
                modified_sentences.append(sentence)
                update_sentence_action(sentence, pruning, request.user, new_action)

        # Save pruning
        prune_pruning(pruning)

        # Set human indices
        set_ml_indices_as_human(pruning)

        if modified_sentences:
            # reset page counter
            reset_pages_counter_of_pruning(pruning)

            # re-prune affected prunings
            reprune_affected_prunings(modified_sentences, pruning)

    colored_pieces = get_colored_pieces(extracted_html,
                                        SentenceFromDbActionInterface(pruning))

    action_colors = {
        Action.START: 'info',
        Action.SHOW: 'success',
        Action.HIDE: 'black',
        Action.STOP: 'danger',
    }

    return render(request, 'pages/edit_pruning_v1.html', {
        'pruning': pruning,
        'colored_pieces': colored_pieces,
        'action_colors': action_colors,
    })


@login_required
@staff_member_required
def edit_pruning_human(request, pruning_uuid):
    try:
        pruning = Pruning.objects.get(uuid=pruning_uuid)
    except Page.DoesNotExist:
        return HttpResponseNotFound("Pruning not found")

    if request.method == "POST":
        new_indices = []
        for i in range(len(split_lines(pruning.extracted_html))):
            if request.POST.get(f"line-{i}", False):
                new_indices.append(i)

        set_human_indices(pruning, new_indices)

    pruning_human_pieces = get_pruning_human_pieces(pruning)

    return render(request, 'pages/edit_pruning_human.html', {
        'pruning': pruning,
        'pruning_human_pieces': pruning_human_pieces,
    })


@login_required
@permission_required("home.change_sentence")
def edit_pruning_v2(request, pruning_uuid):
    try:
        pruning = Pruning.objects.get(uuid=pruning_uuid)
    except Page.DoesNotExist:
        return HttpResponseNotFound("Pruning not found")

    extracted_html = pruning.extracted_html

    if request.method == "POST":
        dummy_colored_pieces = get_colored_pieces_v2(extracted_html,
                                                     DummyQualifyLineInterface())
        modified_sentences = []
        for dummy_piece in dummy_colored_pieces:
            sentence_uuid = request.POST.get(f"sentence-uuid-{dummy_piece.id}")
            sentence = Sentence.objects.get(uuid=sentence_uuid)
            new_specifier = request.POST.get(f"specifier-{dummy_piece.id}") == 'on'
            new_schedule = request.POST.get(f"schedule-{dummy_piece.id}") == 'on'
            new_event_motion = EventMotion(request.POST.get(f"event-motion-{dummy_piece.id}"))

            if sentence.human_specifier != new_specifier \
                    or sentence.human_schedule != new_schedule \
                    or (sentence.human_confession is None
                        or EventMotion(sentence.human_confession) != new_event_motion):
                modified_sentences.append(sentence)
                sentence.human_specifier = new_specifier
                sentence.human_schedule = new_schedule
                sentence.human_confession = new_event_motion.value
                sentence.save()

        # Save pruning
        prune_pruning(pruning)

        if request.POST.get("set_as_human", '') == 'true':
            # Set human indices
            set_v2_indices_as_human(pruning)

        if modified_sentences:
            # reset page counter
            reset_pages_counter_of_pruning(pruning)

            # re-prune affected prunings
            reprune_affected_prunings(modified_sentences, pruning)

    colored_pieces = get_colored_pieces_v2(extracted_html,
                                           SentenceQualifyLineInterface(pruning))

    event_motion_colors = {
        EventMotion.START: 'success',
        EventMotion.SHOW: 'info',
        EventMotion.HOLD: 'info',
        EventMotion.HIDE: 'gray-500',
        EventMotion.STOP: 'danger',
    }

    return render(request, 'pages/edit_pruning_v2.html', {
        'pruning': pruning,
        'colored_pieces': colored_pieces,
        'event_motion_colors': event_motion_colors,
    })


@login_required
@permission_required("home.change_sentence")
def edit_parsing(request, parsing_uuid):
    try:
        parsing = Parsing.objects.get(uuid=parsing_uuid)
    except Parsing.DoesNotExist:
        return HttpResponseNotFound("Parsing not found")

    schedules_list_as_json = None
    validation_error = None
    success = False

    if request.method == "POST":
        schedules_list_as_json = request.POST.get("json")
        schedules_list_as_dict = json.loads(schedules_list_as_json)
        previous_schedule_list = get_parsing_schedules_list(parsing)
        try:
            schedules_list = SchedulesList(**schedules_list_as_dict)
            parsing.human_json = schedules_list.model_dump(mode='json')
            parsing.save()
            success = True
            re_index_related_website(parsing)

            if schedules_list != previous_schedule_list:
                # reset page counter
                reset_counters_of_parsing(parsing)
        except ValidationError as e:
            validation_error = str(e)

    if not schedules_list_as_json:
        schedules_list = get_parsing_schedules_list(parsing)
        schedules_list_as_json = schedules_list.model_dump_json()

    # This is a ugly hack since openai doesn't support format in the schema
    json_schema = json.loads(
        json.dumps(SchedulesList.model_json_schema())
        .replace('"description": "uniqueItems"', '"uniqueItems": true')
        .replace('description', 'format')
    )
    form = JSONSchemaForm(
        schema=json_schema,
        options={
            "theme": "bootstrap4",
            "enable_array_copy": True,
            "disable_edit_json": True,
            "disable_properties": True,
            "disable_array_delete_last_row": True,
            "prompt_before_delete": False,
            "no_additional_properties": True,
            "iconlib": "fontawesome5",
        },
        ajax=False,
        data={"json": schedules_list_as_json}
    )

    return render(request, 'pages/edit_parsing.html', {
        'parsing': parsing,
        'form': form,
        'validation_error': validation_error,
        'success': success,
    })
