from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponseNotFound
from django.shortcuts import render

from home.models import Page, Pruning
from home.services.edit_pruning_service import get_colored_pieces, save_sentence, \
    reset_pages_counter_of_pruning
from scraping.extract.extract_content import KeyValueInterface, DummyActionInterface
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
        action_per_line_without_link = {}
        colored_pieces = get_colored_pieces(extracted_html,
                                            DummyActionInterface())
        for piece in colored_pieces:
            action = Action(request.POST.get(f"action-{piece.id}"))
            action_per_line_without_link[piece.text_without_link] = action

        # We compute new color based on these given POST actions
        colored_pieces = get_colored_pieces(extracted_html,
                                            KeyValueInterface(action_per_line_without_link))
        modified_sentences = []
        for piece in colored_pieces:
            line_without_link = piece.text_without_link
            action = action_per_line_without_link[line_without_link]
            if piece.do_show or action != Action.SHOW:
                # We only save the SHOW lines that are shown, and all other lines
                # TODO refacto: get the Sentence uuid and pass it in the POST
                sentence = save_sentence(line_without_link, pruning, request.user,
                                         action)
                if sentence is not None:
                    modified_sentences.append(sentence)

        if modified_sentences:
            # reset page counter
            reset_pages_counter_of_pruning(pruning)

        prune_pruning(pruning)
        reprune_affected_scrapings(modified_sentences, pruning)

    else:
        colored_pieces = get_colored_pieces(extracted_html,
                                            SentenceFromDbActionInterface(pruning))

    action_colors = {
        Action.SHOW: 'success',
        Action.HIDE: 'black',
        Action.STOP: 'danger',
    }

    return render(request, 'pages/edit_pruning.html', {
        'pruning': pruning,
        'colored_pieces': colored_pieces,
        'action_colors': action_colors,
    })
