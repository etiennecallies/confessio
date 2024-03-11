from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponseNotFound, HttpResponseBadRequest
from django.shortcuts import render

from home.models import Page
from home.services.qualify_service import get_colored_pieces, save_sentence
from scraping.services.prune_scraping_service import prune_scraping_and_save


@login_required
@permission_required("home.change_sentence")
def qualify_page(request, page_uuid):
    try:
        page = Page.objects.get(uuid=page_uuid, deleted_at__isnull=True)
    except Page.DoesNotExist:
        return HttpResponseNotFound("Page not found")

    latest_scraping = page.get_latest_scraping()
    if latest_scraping is None:
        return HttpResponseBadRequest("No scraping for this page")

    confession_html = latest_scraping.confession_html
    confession_html_hash = hash(confession_html)

    if request.method == "POST":
        confession_html_hash_post = request.POST.get('confession_html_hash')
        if not confession_html_hash_post or confession_html_hash != int(confession_html_hash_post):
            return HttpResponseBadRequest("confession_html has changed in the mean time")

        # We get previous color
        colored_pieces = get_colored_pieces(confession_html)
        for piece in colored_pieces:
            line_without_link = piece['text_without_link']

            checked_per_tag = {}
            for tag_name, tag in piece['tags'].items():
                checked_per_tag[tag_name] = request.POST.get(tag['id']) == 'on'

            save_sentence(line_without_link, latest_scraping, request.user, checked_per_tag)

        prune_scraping_and_save(latest_scraping)

    # We get piece with fresh color
    colored_pieces = get_colored_pieces(confession_html)

    context = {
        'page': page,
        'parish': page.parish,
        'confession_html_hash': confession_html_hash,
        'colored_pieces': colored_pieces,
    }

    return render(request, 'pages/qualify_page.html', context)
