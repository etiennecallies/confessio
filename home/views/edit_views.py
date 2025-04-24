import json

from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponseNotFound
from django.shortcuts import render
from pydantic import ValidationError

from home.models import Page, Pruning, Sentence, Parsing
from home.services.edit_pruning_service import get_colored_pieces, update_sentence_action, \
    reset_pages_counter_of_pruning, set_human_indices
from jsoneditor.forms import JSONSchemaForm
from scraping.parse.schedules import SchedulesList
from scraping.prune.action_interfaces import DummyActionInterface
from scraping.prune.models import Action
from scraping.services.parse_pruning_service import reset_counters_of_parsing
from scraping.services.parsing_service import get_parsing_schedules_list
from scraping.services.prune_scraping_service import SentenceFromDbActionInterface, \
    reprune_affected_prunings, prune_pruning


@login_required
@permission_required("home.change_sentence")
def edit_pruning(request, pruning_uuid):
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
        set_human_indices(pruning)

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

    return render(request, 'pages/edit_pruning.html', {
        'pruning': pruning,
        'colored_pieces': colored_pieces,
        'action_colors': action_colors,
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
            parsing.human_json = schedules_list.model_dump()
            parsing.save()
            success = True

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
