from django.contrib.auth.decorators import login_required
from django.http import HttpResponseNotFound, HttpResponseBadRequest
from django.shortcuts import render

from home.models import Page, Sentence
from home.services.map_service import get_churches_in_box, prepare_map, get_churches_around
from home.services.tag_service import color_pieces, update_sentence
from scraping.utils.extract_content import get_confession_pieces


def index(request):
    location = request.GET.get('location', '')
    latitude = request.GET.get('latitude', '')
    longitude = request.GET.get('longitude', '')

    min_lat = request.GET.get('minLat', '')
    min_lng = request.GET.get('minLng', '')
    max_lat = request.GET.get('maxLat', '')
    max_lng = request.GET.get('maxLng', '')

    if min_lat and min_lng and max_lat and max_lng:
        min_lat, max_lat, min_lng, max_lng = \
            float(min_lat), float(max_lat), float(min_lng), float(max_lng)
        bounds = (min_lat, max_lat, min_lng, max_lng)
        center = [min_lat + max_lat / 2, min_lng + max_lng / 2]
        churches = get_churches_in_box(min_lat, max_lat, min_lng, max_lng)
    else:
        bounds = None

        if latitude and longitude:
            center = [float(latitude), float(longitude)]
        else:
            # Default coordinates (Paris)
            center = [48.859, 2.342]

        churches = get_churches_around(center)

    folium_map, church_marker_names = prepare_map(center, churches, bounds)

    # Get HTML Representation of Map Object
    map_html = folium_map._repr_html_()

    # Hack 1: we add an id to iframe of map since we need to get the element in javascript
    # Hack 2: we add the name of the map js object as attribute since we will need to retrieve it
    map_html = map_html.replace(
        '<iframe srcdoc=',
        f'<iframe id="map-iframe" data-map-name="{folium_map.get_name()}" srcdoc='
    )

    # We get all parishes and their churches
    parishes_by_uuid = {}
    parish_churches = {}
    for church in churches:
        parishes_by_uuid[church.parish.uuid] = church.parish
        parish_churches.setdefault(church.parish.uuid, []).append(church)

    context = {
        'location': location,
        'map_html': map_html,
        'church_marker_names': church_marker_names,
        'parishes': parishes_by_uuid.values(),
        'parish_churches': parish_churches,
    }

    return render(request, 'pages/index.html', context)


@login_required
def qualify_page(request, page_uuid):
    try:
        page = Page.objects.get(uuid=page_uuid)
    except Page.DoesNotExist:
        return HttpResponseNotFound("Page not found")

    latest_scraping = page.get_latest_scraping()
    if latest_scraping is None:
        return HttpResponseBadRequest("No scraping for this page")

    confession_html = latest_scraping.confession_html
    confession_pieces = get_confession_pieces(confession_html)
    colored_pieces = color_pieces(confession_pieces)
    confession_html_hash = hash(confession_html)

    if request.method == "POST":
        confession_html_hash_post = request.POST.get('confession_html_hash')
        if not confession_html_hash_post or confession_html_hash != int(confession_html_hash_post):
            return HttpResponseBadRequest("confession_html has changed in the mean time")

        # TODO save
        # TODO re-compute confession_html
        new_confession_pieces = []
        for piece in colored_pieces:
            line = piece['text']
            try:
                sentence = Sentence.objects.get(line=line)
            except Sentence.DoesNotExist:
                sentence = Sentence(line=line)

            checked_per_tag = {}
            for tag_name, tag in piece['tags'].items():
                checked_per_tag[tag_name] = request.POST.get(tag['id']) == 'on'
            update_sentence(sentence, checked_per_tag)

            sentence.save()

            all_checks = [t for t, checked in checked_per_tag.items() if checked]
            new_confession_pieces.append((line, all_checks))

        colored_pieces = color_pieces(new_confession_pieces)

    context = {
        'page': page,
        'parish': page.parish,
        'confession_html_hash': confession_html_hash,
        'colored_pieces': colored_pieces,
    }

    return render(request, 'pages/qualify_page.html', context)
