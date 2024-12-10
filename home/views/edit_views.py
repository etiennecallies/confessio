import json

from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponseNotFound
from django.shortcuts import render
from django_jsonforms.forms import JSONSchemaForm

from home.models import Page, Pruning, Sentence, Parsing
from home.services.edit_pruning_service import get_colored_pieces, update_sentence_action, \
    reset_pages_counter_of_pruning
from scraping.parse.schedules import SchedulesList
from scraping.prune.action_interfaces import DummyActionInterface
from scraping.prune.models import Action
from scraping.services.prune_scraping_service import SentenceFromDbActionInterface, \
    reprune_affected_scrapings, prune_pruning


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

        if modified_sentences:
            # reset page counter
            reset_pages_counter_of_pruning(pruning)

        prune_pruning(pruning)
        reprune_affected_scrapings(modified_sentences, pruning)

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

    if request.method == "POST":
        schedules_list_as_json = request.POST.get("json")
        schedules_list_as_dict = json.loads(schedules_list_as_json)
        schedules_list = SchedulesList(**schedules_list_as_dict)
        parsing.human_json = schedules_list.model_dump()
        parsing.save()

    # TODO make a function to get the schedules_list from parsing
    schedules_list = SchedulesList(**(parsing.human_json or parsing.llm_json))
    form = JSONSchemaForm(
        schema=SchedulesList.model_json_schema(),
        options={"theme": "bootstrap3"},
        ajax=False,
        data={"json": schedules_list.model_dump_json()}
    )

    return render(request, 'pages/edit_parsing.html', {
        'parsing': parsing,
        'form': form,
    })
