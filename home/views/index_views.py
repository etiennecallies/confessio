import dataclasses

from django.core.exceptions import ValidationError
from django.http import HttpResponseNotFound, JsonResponse
from django.shortcuts import render

from home.models import Website, Diocese
from home.services.autocomplete_service import get_aggregated_response
from home.services.map_service import get_churches_in_box, get_churches_around, prepare_map, \
    get_churches_by_website, get_center, get_churches_by_diocese, MAX_CHURCHES_IN_RESULTS
from home.services.page_url_service import get_page_url_with_pointer


def render_map(request, center, churches, bounds, location, too_many_results: bool):
    folium_map, church_marker_names = prepare_map(center, churches, bounds)

    # Get HTML Representation of Map Object
    map_html = folium_map._repr_html_()

    # Hack 1: we add an id to iframe of map since we need to get the element in javascript
    # Hack 2: we add the name of the map js object as attribute since we will need to retrieve it
    map_html = map_html.replace(
        '<iframe srcdoc=',
        f'<iframe id="map-iframe" data-map-name="{folium_map.get_name()}" srcdoc='
    )

    # Hack 3: we add a class to force map to be a squared on mobile in CSS
    map_html = map_html.replace(
        '<div style="position:relative;width:100%;height:0;padding-bottom:60%;">',
        '<div class="map-container">'
    )

    # We get all websites and their churches
    websites_by_uuid = {}
    website_churches = {}
    for church in churches:
        websites_by_uuid[church.parish.website.uuid] = church.parish.website
        website_churches.setdefault(church.parish.website.uuid, []).append(church)
    websites = websites_by_uuid.values()

    # Page url with #:~:text=
    page_urls = {}
    for website in websites:
        for page in website.get_pages():
            page_urls[page.uuid] = get_page_url_with_pointer(page)

    context = {
        'location': location,
        'map_html': map_html,
        'church_marker_names': church_marker_names,
        'websites': websites,
        'website_churches': website_churches,
        'page_urls': page_urls,
        'too_many_results': too_many_results,
    }

    return render(request, 'pages/index.html', context)


def index(request, diocese_slug=None):
    location = request.GET.get('location', '')
    latitude = request.GET.get('latitude', '')
    longitude = request.GET.get('longitude', '')

    min_lat = request.GET.get('minLat', '')
    min_lng = request.GET.get('minLng', '')
    max_lat = request.GET.get('maxLat', '')
    max_lng = request.GET.get('maxLng', '')

    website_uuid = request.GET.get('websiteUuid', '')

    if min_lat and min_lng and max_lat and max_lng:
        min_lat, max_lat, min_lng, max_lng = \
            float(min_lat), float(max_lat), float(min_lng), float(max_lng)
        bounds = (min_lat, max_lat, min_lng, max_lng)
        center = [min_lat + max_lat / 2, min_lng + max_lng / 2]
        churches, too_many_results = get_churches_in_box(min_lat, max_lat, min_lng, max_lng)
    elif website_uuid:
        try:
            website = Website.objects.get(uuid=website_uuid, is_active=True)
        except (ValidationError, Website.DoesNotExist):
            return HttpResponseNotFound("Website does not exist with this uuid")

        churches, too_many_results = get_churches_by_website(website)
        if len(churches) == 0:
            return HttpResponseNotFound("No church found for this website")

        center = get_center(churches)
        bounds = None
    elif latitude and longitude:
        center = [float(latitude), float(longitude)]
        churches, too_many_results = get_churches_around(center)
        bounds = None
    elif diocese_slug:
        try:
            diocese = Diocese.objects.get(slug=diocese_slug)
        except Diocese.DoesNotExist:
            return HttpResponseNotFound("Diocese not found")

        churches, too_many_results = get_churches_by_diocese(diocese)
        if len(churches) == 0:
            return HttpResponseNotFound("No church found for this diocese")
        center = get_center(churches)
        bounds = None
    else:
        # Default coordinates
        # center = [48.859, 2.342]  # Paris
        center = [45.758, 4.832]  # Lyon - Bellecour
        churches, too_many_results = get_churches_around(center)
        bounds = None

    return render_map(request, center, churches, bounds, location, too_many_results)


def autocomplete(request):
    query = request.GET.get('query', '')
    results = get_aggregated_response(query)
    response = list(map(dataclasses.asdict, results))

    return JsonResponse(response, safe=False)


def dioceses_list(request):
    dioceses = Diocese.objects.all()

    context = {
        'dioceses': dioceses,
    }

    return render(request, 'pages/dioceses.html', context)
