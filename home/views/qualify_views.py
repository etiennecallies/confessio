from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponseNotFound, HttpResponseBadRequest
from django.shortcuts import render

from home.models import Page
from home.services.qualify_service import get_colored_pieces, save_sentence
from scraping.extract.extract_content import KeyValueInterface, DummyTagInterface
from scraping.prune.models import Action
from scraping.services.prune_scraping_service import prune_scraping_and_save, \
    SentenceFromDbTagInterface, reprune_affected_scrapings
from home.utils.hash_utils import hash_string_to_hex


@login_required
@permission_required("home.change_sentence")
def qualify_page(request, page_uuid):
    try:
        page = Page.objects.get(uuid=page_uuid)
    except Page.DoesNotExist:
        return HttpResponseNotFound("Page not found")

    latest_scraping = page.get_latest_scraping()
    if latest_scraping is None:
        return HttpResponseBadRequest("No scraping for this page")

    confession_html = latest_scraping.confession_html
    if not confession_html:
        return HttpResponseNotFound("No more confession_html on this page")

    confession_html_hash = hash_string_to_hex(confession_html)

    if request.method == "POST":
        confession_html_hash_post = request.POST.get('confession_html_hash')
        if not confession_html_hash_post or confession_html_hash != confession_html_hash_post:
            return HttpResponseBadRequest("confession_html has changed in the mean time")

        # We extract action per line from POST
        action_per_line_without_link = {}
        colored_pieces = get_colored_pieces(confession_html,
                                            DummyTagInterface())
        for piece in colored_pieces:
            action = Action(request.POST.get(f"action-{piece['id']}"))
            action_per_line_without_link[piece['text_without_link']] = action

        # We compute new color based on these given POST actions
        colored_pieces = get_colored_pieces(confession_html,
                                            KeyValueInterface(action_per_line_without_link))
        modified_sentences = []
        for piece in colored_pieces:
            line_without_link = piece['text_without_link']
            action = action_per_line_without_link[line_without_link]
            if piece['do_show'] or action != Action.SHOW:
                # We only save the SHOW lines that are shown, and all other lines
                sentence = save_sentence(line_without_link, latest_scraping, request.user, action)
                if sentence is not None:
                    modified_sentences.append(sentence)

        prune_scraping_and_save(latest_scraping)
        reprune_affected_scrapings(modified_sentences, latest_scraping)

    else:
        colored_pieces = get_colored_pieces(confession_html,
                                            SentenceFromDbTagInterface(latest_scraping.pruning))

    action_colors = {
        Action.SHOW: 'success',
        Action.HIDE: 'black',
        Action.STOP: 'danger',
    }

    context = {
        'page': page,
        'website': page.website,
        'confession_html_hash': confession_html_hash,
        'colored_pieces': colored_pieces,
        'action_colors': action_colors,
    }

    return render(request, 'pages/qualify_page.html', context)
