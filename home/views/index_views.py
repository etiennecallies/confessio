import dataclasses
from datetime import date

from django.core.exceptions import ValidationError
from django.http import HttpResponseNotFound, JsonResponse
from django.shortcuts import render

from home.models import Website, Diocese
from home.services.autocomplete_service import get_aggregated_response
from home.services.events_service import get_website_merged_church_schedules_list
from home.services.filter_service import get_filter_days
from home.services.map_service import get_churches_in_box, get_churches_around, prepare_map, \
    get_churches_by_website, get_center, get_churches_by_diocese
from home.services.page_url_service import get_page_pruning_urls
from home.services.report_service import get_count_and_label
from home.utils.date_utils import get_current_day, get_current_year


def render_map(request, center, churches, bounds, location, too_many_results: bool,
               is_around_me: bool, day_filter: date | None):
    # We get all websites and their churches
    websites_by_uuid = {}
    website_churches = {}
    for church in churches:
        websites_by_uuid[church.parish.website.uuid] = church.parish.website
        website_churches.setdefault(church.parish.website.uuid, []).append(church)
    websites = list(websites_by_uuid.values())

    # We compute the merged schedules list for each website
    website_merged_church_schedules_list = get_website_merged_church_schedules_list(
        websites, website_churches, day_filter)

    if day_filter:
        # Filter on websites that have actual schedules
        websites = [w for w in websites if w.uuid in website_merged_church_schedules_list]

    # We prepare the map
    folium_map, church_marker_names = prepare_map(center, churches, bounds,
                                                  website_merged_church_schedules_list,
                                                  is_around_me)

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

    # Get page url with #:~:text=
    page_pruning_urls = get_page_pruning_urls(websites)
    # Count reports for each website
    website_reports_count = {}
    for website in websites:
        website_reports_count[website.uuid] = get_count_and_label(website)

    hidden_inputs = {}
    for key in request.GET:
        if key not in ['dateFilter']:
            hidden_inputs[key] = request.GET[key]

    context = {
        'location': location,
        'map_html': map_html,
        'church_marker_names': church_marker_names,
        'websites': websites,
        'website_merged_church_schedules_list': website_merged_church_schedules_list,
        'page_pruning_urls': page_pruning_urls,
        'too_many_results': too_many_results,
        'website_reports_count': website_reports_count,
        'current_day': get_current_day(),
        'current_year': str(get_current_year()),
        'filter_days': get_filter_days(day_filter),
        'date_filter_value': day_filter.isoformat() if day_filter else '',
        'action_path': request.path,
        'hidden_inputs': hidden_inputs,
    }

    return render(request, 'pages/index.html', context)


def extract_float(key: str, request) -> float | None:
    value = request.GET.get(key, '')
    try:
        return float(value)
    except ValueError:
        return None


def extract_day_filter(request) -> date | None:
    date_filter = request.GET.get('dateFilter', '')
    if date_filter and date_filter != 'any':
        try:
            return date.fromisoformat(date_filter)
        except ValueError:
            pass

    return None


def index(request, diocese_slug=None, is_around_me: bool = False):
    location = request.GET.get('location', '')
    latitude = extract_float('latitude', request)
    longitude = extract_float('longitude', request)

    min_lat = extract_float('minLat', request)
    min_lng = extract_float('minLng', request)
    max_lat = extract_float('maxLat', request)
    max_lng = extract_float('maxLng', request)

    website_uuid = request.GET.get('websiteUuid', '')

    day_filter = extract_day_filter(request)

    if min_lat and min_lng and max_lat and max_lng:
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
        center = [latitude, longitude]
        churches, _ = get_churches_around(center)
        too_many_results = False
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
        center = [48.859, 2.342]  # Paris
        # center = [45.758, 4.832]  # Lyon - Bellecour
        churches, _ = get_churches_around(center)
        too_many_results = False
        bounds = None

    return render_map(request, center, churches, bounds, location, too_many_results, is_around_me,
                      day_filter)


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
