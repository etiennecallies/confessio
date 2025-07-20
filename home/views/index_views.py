import dataclasses
import json
from datetime import date
from uuid import UUID

from django.core.exceptions import ValidationError
from django.http import HttpResponseNotFound, JsonResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.utils.translation import gettext

from home.forms.image_upload_form import ImageUploadForm
from home.models import Website, Diocese, ChurchIndexEvent, Church
from home.services.autocomplete_service import get_aggregated_response
from home.services.filter_service import get_filter_days
from home.services.upload_image_service import upload_image
from home.services.map_service import prepare_map, get_center, get_cities_label
from home.services.page_url_service import get_page_pruning_urls
from home.services.report_service import get_count_and_label, new_report, NewReportError, \
    get_previous_reports
from home.services.search_service import TimeFilter, get_churches_in_box, get_churches_by_website, \
    get_churches_around, get_churches_by_diocese, get_popular_churches, fetch_events
from home.services.sources_service import get_website_parsings_and_prunings, get_empty_sources
from home.services.stat_service import new_search_hit
from home.services.website_events_service import get_website_events
from home.services.website_schedules_service import get_website_schedules
from home.utils.date_utils import get_current_day, get_current_year
from home.utils.web_utils import redirect_with_url_params
from sourcing.utils.string_utils import lower_first, city_and_prefix


def render_map(request, center,
               index_events: list[ChurchIndexEvent],
               events_truncated_by_website_uuid: dict[UUID, bool],
               churches, h1_title: str,
               meta_title: str, display_sub_title: bool,
               bounds, location, too_many_results: bool,
               is_around_me: bool, time_filter: TimeFilter,
               page_website: Website | None, success_message: str | None,
               welcome_message: str | None, display_quick_search_cities: bool):
    upload_success = extract_bool('upload_success', request)
    upload_error_message = request.GET.get('upload_error_message', None)
    success_message = success_message or (
        "L'image a été chargée avec succès !" if upload_success else None
    )

    # We get all websites and their churches
    websites_by_uuid = {}
    website_churches = {}
    for church in churches:
        websites_by_uuid[church.parish.website.uuid] = church.parish.website
        website_churches.setdefault(church.parish.website.uuid, []).append(church)
    websites = list(websites_by_uuid.values())

    website_city_label = {}
    church_uuids_json_by_website = {}
    for website_uuid, churches_list in website_churches.items():
        website_city_label[website_uuid] = get_cities_label(churches_list)
        church_uuids_json_by_website[website_uuid] = \
            json.dumps([str(church.uuid) for church in churches_list])

    index_events_by_website = {}
    for index_event in index_events:
        index_events_by_website.setdefault(index_event.church.parish.website.uuid, [])\
            .append(index_event)

    events_by_website = {}
    for website in websites:
        events_by_website[website.uuid] = get_website_events(
            index_events_by_website.get(website.uuid, []),
            events_truncated_by_website_uuid[website.uuid],
            time_filter.day_filter is not None
        )

    # We prepare the map
    folium_map, church_marker_names_json_by_website = prepare_map(
        center, churches, bounds, events_by_website, is_around_me)

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

    # Hack 4: add border radius to map
    text_to_find = ('style="position:absolute;width:100%;height:100%;left:0;top:0;'
                    'border:none !important;')
    map_html = map_html.replace(text_to_find, text_to_find + 'border-radius:1em;')

    # Count reports for each website
    website_reports_count = {}
    for website in websites:
        website_reports_count[website.uuid] = get_count_and_label(website)

    hidden_inputs = {}
    for key in request.GET:
        if key not in ['dateFilter', 'hourMin', 'hourMax']:
            hidden_inputs[key] = request.GET[key]

    if request.resolver_match.url_name != 'index' and upload_success is None:
        new_search_hit(request, len(websites))

    return render(request, 'pages/index.html', {
        'h1_title': h1_title,
        'meta_title': meta_title,
        'display_sub_title': display_sub_title,
        'location': location,
        'map_html': map_html,
        'church_marker_names_json_by_website': church_marker_names_json_by_website,
        'church_uuids_json_by_website': church_uuids_json_by_website,
        'websites': websites,
        'events_by_website': events_by_website,
        'website_city_label': website_city_label,
        'too_many_results': too_many_results,
        'welcome_message': welcome_message,
        'display_quick_search_cities': display_quick_search_cities,
        'website_reports_count': website_reports_count,
        'current_day': get_current_day(),
        'current_year': str(get_current_year()),
        'filter_days': get_filter_days(time_filter.day_filter),
        'date_filter_value': time_filter.day_filter.isoformat() if time_filter.day_filter else '',
        'hour_min': time_filter.hour_min or '',
        'hour_max': time_filter.hour_max or '',
        'action_path': request.path,
        'hidden_inputs': hidden_inputs,
        'page_website': page_website,
        'success_message': success_message,
        'previous_reports': get_previous_reports(page_website) if page_website else None,
        'image_upload_form': ImageUploadForm() if page_website else None,
        'upload_error_message': upload_error_message,
        'website_images': page_website.images.all() if page_website else None,
    })


def extract_float(key: str, request) -> float | None:
    value = request.GET.get(key, '')
    try:
        return float(value)
    except ValueError:
        return None


def extract_int(key: str, request, default: int) -> int | None:
    value = request.GET.get(key, '')
    try:
        val = int(value)
        if val == default:
            return None
        return val
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


def extract_bool(key: str, request) -> bool | None:
    value = request.GET.get(key, '')
    if value.lower() == 'true':
        return True
    elif value.lower() == 'false':
        return False
    else:
        return None


def extract_temporal_filters(request) -> TimeFilter:
    return TimeFilter(
        day_filter=extract_day_filter(request),
        hour_min=extract_int('hourMin', request, 0),
        hour_max=extract_int('hourMax', request, 24 * 60 - 1),
    )


def index(request, diocese_slug=None, website_uuid: str = None, is_around_me: bool = False):
    location = request.GET.get('location', '')
    latitude = extract_float('latitude', request)
    longitude = extract_float('longitude', request)

    min_lat = extract_float('minLat', request)
    min_lng = extract_float('minLng', request)
    max_lat = extract_float('maxLat', request)
    max_lng = extract_float('maxLng', request)
    time_filter = extract_temporal_filters(request)

    website = None
    success_message = None

    h1_title = gettext("confessioTitle")
    meta_title = gettext("confessioPageTitle")
    welcome_message = None
    display_quick_search_cities = False

    if min_lat and min_lng and max_lat and max_lng:
        bounds = (min_lat, max_lat, min_lng, max_lng)
        center = [min_lat + max_lat / 2, min_lng + max_lng / 2]
        index_events, churches, too_many_results, events_truncated_by_website_uuid = \
            get_churches_in_box(min_lat, max_lat, min_lng, max_lng, time_filter)

        display_sub_title = False
    elif website_uuid:
        try:
            website = Website.objects.get(uuid=website_uuid, is_active=True)
        except (ValidationError, Website.DoesNotExist):
            return HttpResponseNotFound("Website does not exist with this uuid")

        if request.method == "POST":
            try:
                success_message = new_report(request, website)
            except NewReportError as e:
                return e.response

        index_events, churches, too_many_results, events_truncated_by_website_uuid = \
            get_churches_by_website(website, time_filter)

        if len(churches) == 0:
            website_churches = [church for p in website.parishes.all()
                                for church in p.churches.all()]
            if len(website_churches) == 0:
                return HttpResponseNotFound("No church found for this website")

            center = get_center(website_churches)
        else:
            center = get_center(churches)
        bounds = None

        h1_title = f'{website.name}'
        meta_title = f"{h1_title} | {gettext('confessioTitle')}"
        display_sub_title = False
    elif latitude and longitude:
        center = [latitude, longitude]
        index_events, churches, _, events_truncated_by_website_uuid = \
            get_churches_around(center, time_filter)
        too_many_results = False
        bounds = None

        if location:
            h1_title = f'Se confesser {city_and_prefix(location)}'
            meta_title = f"{h1_title} | {gettext('confessioTitle')}"
        display_sub_title = False
    elif diocese_slug:
        try:
            diocese = Diocese.objects.get(slug=diocese_slug)
        except Diocese.DoesNotExist:
            return HttpResponseNotFound("Diocese not found")

        index_events, churches, too_many_results, events_truncated_by_website_uuid = \
            get_churches_by_diocese(diocese, time_filter)
        if len(churches) == 0:
            diocese_churches = [church for p in diocese.parishes.all()
                                for church in p.churches.all()]
            if len(diocese_churches) == 0:
                return HttpResponseNotFound("No church found for this diocese")

            center = get_center(diocese_churches)
        else:
            center = get_center(churches)
        bounds = None

        h1_title = f'Se confesser au {lower_first(diocese.name)}'
        meta_title = f"{h1_title} | {gettext('confessioTitle')}"
        display_sub_title = False
        if time_filter.is_null():
            too_many_results = False
            welcome_message = f"""👋 Voici quelques horaires de confession au
{lower_first(diocese.name)}. N'hésitez pas à préciser votre recherche grâce aux filtres.
Merci de nous remonter d'éventuelles erreurs. Bonne confession !"""

    else:
        index_events, churches, too_many_results, events_truncated_by_website_uuid = \
            get_popular_churches(time_filter)
        if churches:
            center = get_center(churches)
        else:
            # Default coordinates
            center = [48.859, 2.342]  # Paris
        bounds = None

        display_sub_title = True
        if time_filter.is_null():
            too_many_results = False
            welcome_message = """👋 Bienvenue ! Confessio affiche les horaires des confessions
indiqués sur les sites web des paroisses, et sera national en décembre 2025. N'hésitez pas à
remonter d'éventuelles erreurs. Merci et bonne confession !"""
            display_quick_search_cities = True

    return render_map(request, center, index_events, events_truncated_by_website_uuid, churches,
                      h1_title, meta_title, display_sub_title,
                      bounds, location, too_many_results, is_around_me,
                      time_filter, website, success_message, welcome_message,
                      display_quick_search_cities)


def partial_website_sources(request, website_uuid: str):
    try:
        website = Website.objects.get(uuid=website_uuid)
    except Website.DoesNotExist:
        return HttpResponseNotFound("Website does not exist with this uuid")

    empty_sources = None
    if request.user.is_authenticated and request.user.has_perm("home.change_sentence"):
        empty_sources = get_empty_sources(website)

    return render(request, 'partials/website_sources.html', {
        'website': website,
        'parsings_and_prunings': get_website_parsings_and_prunings(website),
        'page_pruning_urls': get_page_pruning_urls([website]),
        'empty_sources': empty_sources,
    })


def partial_website_churches(request, website_uuid: str):
    try:
        website = Website.objects.get(uuid=website_uuid)
    except Website.DoesNotExist:
        return HttpResponseNotFound("Website does not exist with this uuid")

    display_explicit_other_churches = extract_bool('display_explicit_other_churches', request)

    website_churches = [c for p in website.parishes.all() for c in p.churches.all()]
    website_schedules = get_website_schedules(website, website_churches)

    return render(request, 'partials/website_churches.html', {
        'website': website,
        'website_schedules': website_schedules,
        'display_explicit_other_churches': display_explicit_other_churches,
    })


def partial_website_events(request, website_uuid: str):
    try:
        website = Website.objects.get(uuid=website_uuid)
    except Website.DoesNotExist:
        return HttpResponseNotFound("Website does not exist with this uuid")

    church_uuids_json = request.GET.get('church_uuids_json', '[]')
    try:
        church_uuids = json.loads(church_uuids_json)
    except json.JSONDecodeError:
        return HttpResponseBadRequest(f"Invalid JSON for church uuids: '{church_uuids_json}'")

    churches = Church.objects.filter(uuid__in=church_uuids).all()
    if len(churches) < len(church_uuids):
        return HttpResponseNotFound(f"Some churches do not exist with these uuids {church_uuids}")

    church_by_uuid = {c.uuid: c for c in churches}
    time_filter = extract_temporal_filters(request)
    index_events = fetch_events(church_by_uuid, time_filter)
    website_events = get_website_events(index_events,
                                        False,
                                        time_filter.day_filter is not None)

    return render(request, 'partials/website_events.html', {
        'website': website,
        'website_events': website_events,
        'current_day': get_current_day(),
        'current_year': str(get_current_year()),
    })


def autocomplete(request):
    query = request.GET.get('query', '')
    results = get_aggregated_response(query)
    response = list(map(dataclasses.asdict, results))

    return JsonResponse(response, safe=False)


def dioceses_list(request):
    dioceses = Diocese.objects.all()

    context = {
        'dioceses': dioceses,
        'meta_title': gettext('diocesesPageTitle'),
    }

    return render(request, 'pages/dioceses.html', context)


def website_upload_image(request, website_uuid: str):
    try:
        website = Website.objects.get(uuid=website_uuid)
    except Website.DoesNotExist:
        return HttpResponseNotFound("Website does not exist with this uuid")

    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)
        comment = request.POST.get('comment', None)
        if form.is_valid():
            image = form.cleaned_data['image']
            success, error_message = upload_image(image, website, comment)

            return redirect_with_url_params(
                "website_view", website_uuid=website_uuid,
                query_params={
                    'upload_success': success,
                    'upload_error_message': error_message if error_message else '',
                })

        return redirect_with_url_params("website_view", website_uuid=website_uuid,
                                        query_params={
                                            'upload_success': False,
                                            'upload_error_message': str(form.errors)
                                        })

    return HttpResponseBadRequest("Invalid request method")
