from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponseNotFound, HttpResponseBadRequest
from django.shortcuts import render

from home.models import Page
from home.services.qualify_service import get_colored_pieces, save_sentence
from scraping.prune.models import Action
from scraping.services.prune_scraping_service import prune_scraping_and_save
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

        # We get previous color
        colored_pieces = get_colored_pieces(confession_html)
        for piece in colored_pieces:
            action = Action(request.POST.get(f"action-{piece['id']}"))
            save_sentence(piece['text_without_link'], latest_scraping, request.user, action)

        prune_scraping_and_save(latest_scraping)

    # We get piece with fresh color
    colored_pieces = get_colored_pieces(confession_html)

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
