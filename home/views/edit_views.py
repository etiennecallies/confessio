from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponseNotFound
from django.shortcuts import render

from home.models import Page, Pruning, Sentence
from home.services.edit_pruning_service import get_colored_pieces, update_sentence_action, \
    reset_pages_counter_of_pruning
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
        if False:
            # TODO Fix too many affected prunings
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
