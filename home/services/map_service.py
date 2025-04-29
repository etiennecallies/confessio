import json
from datetime import date
from statistics import mean
from typing import List, Tuple, Dict, Optional
from uuid import UUID

from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point, Polygon
from django.contrib.gis.measure import D
from django.db.models import QuerySet, OuterRef, Exists
from django.utils.translation import gettext as _
from folium import Map, Icon, Popup, Marker

from home.models import Church, Website, Diocese, ChurchIndexEvent
from home.services.website_events_service import WebsiteEvents
from home.utils.date_utils import format_datetime_with_locale, time_from_minutes

MAX_CHURCHES_IN_RESULTS = 50
MAX_WEBSITES_IN_RESULTS = 50


###############
# QUERY UTILS #
###############


def build_church_query(day_filter: date | None,
                       hour_min: int | None,
                       hour_max: int | None) -> QuerySet[Church]:
    church_query = Church.objects.select_related('parish__website') \
        .prefetch_related('parish__website__reports') \
        .filter(is_active=True,
                parish__website__is_active=True)

    if day_filter or hour_min is not None or hour_max is not None:
        event_query = ChurchIndexEvent.objects.filter(church_id=OuterRef('pk'))
        event_query = add_event_filters(event_query, day_filter, hour_min, hour_max)

        church_query = church_query.annotate(has_event=Exists(event_query)).filter(has_event=True)

    return church_query


def build_events_query(church_by_uuid: dict[UUID, Church],
                       day_filter: date | None,
                       hour_min: int | None,
                       hour_max: int | None) -> QuerySet[ChurchIndexEvent]:
    event_query = ChurchIndexEvent.objects \
        .filter(church__uuid__in=church_by_uuid.keys())
    event_query = add_event_filters(event_query, day_filter, hour_min, hour_max)

    return event_query


def add_event_filters(event_query: QuerySet[ChurchIndexEvent],
                      day_filter: date | None,
                      hour_min: int | None,
                      hour_max: int | None) -> QuerySet[ChurchIndexEvent]:
    if day_filter:
        event_query = event_query.filter(day=day_filter)

    if hour_min is not None or hour_max is not None:
        hour_min = hour_min or 0
        hour_max = hour_max or 24 * 60 - 1
        event_query = event_query.filter(indexed_end_time__gte=time_from_minutes(hour_min),
                                         start_time__lte=time_from_minutes(hour_max))
    return event_query


def truncate_results(church_query: QuerySet[Church],
                     day_filter: date | None,
                     hour_min: int | None,
                     hour_max: int | None
                     ) -> tuple[list[ChurchIndexEvent], list[Church], bool, dict[UUID, bool]]:
    churches = church_query.all()[:MAX_CHURCHES_IN_RESULTS]

    non_truncated_website_uuids = []
    truncated_website_uuids = []
    non_truncated_churches = []
    for church in churches:
        website_uuid = church.parish.website.uuid
        if website_uuid in non_truncated_website_uuids:
            non_truncated_churches.append(church)
            continue

        if website_uuid in truncated_website_uuids:
            continue

        if len(non_truncated_website_uuids) >= MAX_WEBSITES_IN_RESULTS:
            truncated_website_uuids.append(website_uuid)
        else:
            non_truncated_website_uuids.append(website_uuid)
            non_truncated_churches.append(church)

    church_by_uuid = {church.uuid: church for church in non_truncated_churches}
    events = fetch_events(church_by_uuid, day_filter, hour_min, hour_max)
    events_truncated_by_website_uuid = {
        website_uuid: False for website_uuid in non_truncated_website_uuids
    } | {
        website_uuid: True for website_uuid in truncated_website_uuids
    }

    return (events, churches, len(churches) == MAX_CHURCHES_IN_RESULTS,
            events_truncated_by_website_uuid)


def fetch_events(church_by_uuid: dict[UUID, Church],
                 day_filter: date | None,
                 hour_min: int | None,
                 hour_max: int | None) -> list[ChurchIndexEvent]:
    events = build_events_query(church_by_uuid, day_filter, hour_min, hour_max).all()
    for event in events:
        event.church = church_by_uuid.get(event.church_id)

    return events


###########
# QUERIES #
###########

def get_churches_around(center,
                        day_filter: date | None,
                        hour_min: int | None,
                        hour_max: int | None
                        ) -> tuple[list[ChurchIndexEvent], list[Church], bool, dict[UUID, bool]]:
    latitude, longitude = center
    center_as_point = Point(x=longitude, y=latitude)

    church_query = build_church_query(day_filter, hour_min, hour_max) \
        .filter(location__dwithin=(center_as_point, D(km=5))) \
        .annotate(distance=Distance('location', center_as_point)) \
        .order_by('distance')

    return truncate_results(church_query, day_filter, hour_min, hour_max)


def get_churches_in_box(min_lat, max_lat, min_long, max_long,
                        day_filter: date | None,
                        hour_min: int | None,
                        hour_max: int | None
                        ) -> tuple[list[ChurchIndexEvent], list[Church], bool, dict[UUID, bool]]:
    polygon = Polygon.from_bbox((min_long, min_lat, max_long, max_lat))

    church_query = build_church_query(day_filter, hour_min, hour_max)\
        .filter(location__within=polygon)\
        .order_by('-parish__website__nb_recent_hits')

    return truncate_results(church_query, day_filter, hour_min, hour_max)


def get_churches_by_website(
        website: Website,
        day_filter: date | None,
        hour_min: int | None,
        hour_max: int | None
) -> tuple[list[ChurchIndexEvent], list[Church], bool, dict[UUID, bool]]:
    church_query = build_church_query(day_filter, hour_min, hour_max)\
        .filter(parish__website=website)

    return truncate_results(church_query, day_filter, hour_min, hour_max)


def get_churches_by_diocese(
        diocese: Diocese,
        day_filter: date | None,
        hour_min: int | None,
        hour_max: int | None
) -> tuple[list[ChurchIndexEvent], list[Church], bool, dict[UUID, bool]]:
    church_query = build_church_query(day_filter, hour_min, hour_max)\
        .filter(parish__diocese=diocese)\
        .order_by('-parish__website__nb_recent_hits')

    return truncate_results(church_query, day_filter, hour_min, hour_max)


###########
# DISPLAY #
###########

def get_center(churches: List[Church]) -> List[float]:
    latitude = mean(map(lambda c: c.location.y, churches))
    longitude = mean(map(lambda c: c.location.x, churches))

    return [latitude, longitude]


def get_bounds(churches: List[Church]) -> Tuple[float, float, float, float]:
    latitudes = list(map(lambda c: c.location.y, churches))
    longitudes = list(map(lambda c: c.location.x, churches))

    return min(latitudes), max(latitudes), min(longitudes), max(longitudes)


def get_latitude_longitude(point):
    return [point.coords[1], point.coords[0]]


def get_popup_and_color(church: Church,
                        website_events: WebsiteEvents
                        ) -> Tuple[str, str]:
    next_event = website_events.next_event_in_church(church) \
        if website_events else None
    if next_event is not None:
        date_str = format_datetime_with_locale(next_event.start, "%A %d %B", 'fr_FR.UTF-8')
        year_str = f" {next_event.start.year}" \
            if next_event.start.year != date.today().year else ''
        wording = f'{_("NextEvent")}<br>le {date_str.lower()}{year_str} à {next_event.start:%H:%M}'
        color = 'darkblue'
    elif website_events.confession_exists:
        wording = _("ConfessionsExist")
        color = 'blue'
    elif not church.parish.website.has_been_crawled():
        wording = _("NotCrawledYet")
        color = 'beige'
    else:
        wording = _("NoConfessionFound")
        color = 'lightgray'

    link_wording = _("JumpBelow")
    popup_html = f"""
        <b>{church.name}</b><br>
        {wording}<br>
        <a href="#{church.parish.website.uuid}" target="_parent">{link_wording}</a>
    """

    return popup_html, color


def prepare_map(center, churches: List[Church], bounds,
                events_by_website: dict[UUID, WebsiteEvents],
                is_around_me: bool
                ) -> Tuple[Map, Dict[UUID, str]]:
    # Create Map Object
    folium_map = Map(location=center)

    if is_around_me:
        marker = Marker(center,
                        tooltip='Votre position',
                        icon=Icon(icon='crosshairs', prefix='fa', color='lightred'))
        marker.add_to(folium_map)

    # We save marker_names, they will be displayed in template and used in javascript
    church_marker_names_by_website = {}

    for church in churches:
        website_uuid = church.parish.website.uuid
        website_events = events_by_website.get(website_uuid, None)

        tootltip_text = f'{church.name}'
        popup_html, color = get_popup_and_color(church, website_events)
        marker = Marker(get_latitude_longitude(church.location),
                        tooltip=tootltip_text,
                        popup=Popup(html=popup_html, max_width=None),
                        icon=Icon(icon='cross', prefix='fa', color=color))
        church_marker_names_by_website\
            .setdefault(website_uuid, {})[str(church.uuid)] = marker.get_name()
        marker.add_to(folium_map)

    if bounds or len(churches) > 0:
        if bounds:
            min_lat, max_lat, min_long, max_long = bounds
        else:
            min_lat, max_lat, min_long, max_long = get_bounds(churches)
        folium_map.fit_bounds([[min_lat, min_long],
                               [max_lat, max_long]])

    church_marker_names_json_by_website = {
        website_uuid: json.dumps(marker_names)
        for website_uuid, marker_names in church_marker_names_by_website.items()
    }

    return folium_map, church_marker_names_json_by_website


def get_map_with_single_location(location: Point) -> Map:
    folium_map = Map(
        location=get_latitude_longitude(location),
        zoom_start=16,
    )
    marker = Marker(get_latitude_longitude(location),
                    icon=Icon(icon='cross', prefix='fa', color='blue'))
    marker.add_to(folium_map)

    return folium_map


def get_map_with_multiple_locations(churches: list[Church]) -> Optional[Map]:
    if not churches:
        return None

    folium_map = Map(
        location=get_center(churches),
        zoom_start=16,
    )

    for church in churches:
        marker = Marker(get_latitude_longitude(church.location),
                        tooltip=f'{church.name}',
                        icon=Icon(icon='cross', prefix='fa', color='blue'))
        marker.add_to(folium_map)

    min_lat, max_lat, min_long, max_long = get_bounds(churches)
    folium_map.fit_bounds([[min_lat, min_long],
                           [max_lat, max_long]])

    return folium_map


def get_map_with_alternative_locations(church: Church, similar_churches: list[Church]) -> Map:
    folium_map = Map(
        location=get_latitude_longitude(church.location),
        zoom_start=16,
    )
    marker = Marker(get_latitude_longitude(church.location),
                    tooltip=church.name,
                    icon=Icon(icon='cross', prefix='fa', color='blue'))
    marker.add_to(folium_map)

    min_distance = None
    min_church = None
    for i, similar_church in enumerate(similar_churches):
        color = 'green' if similar_church.messesinfo_id is None else 'orange'
        marker = Marker(get_latitude_longitude(similar_church.location),
                        tooltip=f'{similar_church.name}',
                        icon=Icon(icon=f'{i + 1}', prefix='fa', color=color))
        marker.add_to(folium_map)
        distance_to_church = church.location.distance(similar_church.location)
        if min_distance is None or distance_to_church < min_distance:
            min_distance = distance_to_church
            min_church = similar_church

    if min_church:
        folium_map.fit_bounds([
            get_latitude_longitude(church.location),
            get_latitude_longitude(min_church.location)
        ])

    return folium_map


##################
# WEBSITE CITIES #
##################

def get_cities_label(churches: list[Church]) -> str:
    cities_count = {}
    for church in churches:
        if not church.city:
            continue

        church_city = church.city.strip().title()

        cities_count[church_city] = cities_count.get(church_city, 0) + 1

    if len(cities_count) > 4:
        # too many cities
        return ''

    if len(cities_count) == 0:
        # no city
        return ''

    if len(cities_count) == 1:
        # only one city
        return list(cities_count.keys())[0]

    # get city name by order of count
    cities_names = [name for name, count in
                    sorted(cities_count.items(), key=lambda item: item[1], reverse=True)]
    return ' ○ '.join(cities_names)
