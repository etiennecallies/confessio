from statistics import mean
from typing import List, Tuple, Dict, Optional
from uuid import UUID

from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point, Polygon
from django.contrib.gis.measure import D
from django.db.models import Count, Q
from django.utils.translation import gettext as _

from home.models import Church, Website, Diocese
from folium import Map, Icon, Popup, Marker


MAX_CHURCHES_IN_RESULTS = 50


##########
# SEARCH #
##########

def get_churches_around(center) -> tuple[list[Church], bool]:
    latitude, longitude = center
    center_as_point = Point(x=longitude, y=latitude)

    # TODO load parish and latest scraping at the same time
    churches = Church.objects\
        .filter(location__dwithin=(center_as_point, D(km=5)),
                is_active=True,
                parish__website__is_active=True) \
        .annotate(distance=Distance('location', center_as_point)) \
        .order_by('distance')[:MAX_CHURCHES_IN_RESULTS]

    return churches, False


def get_churches_in_box(min_lat, max_lat, min_long, max_long) -> tuple[list[Church], bool]:
    polygon = Polygon.from_bbox((min_long, min_lat, max_long, max_lat))

    # TODO load parish and latest scraping at the same time
    churches = Church.objects\
        .filter(location__within=polygon,
                is_active=True,
                parish__website__is_active=True) \
        .annotate(nb_page_with_confessions=Count(
            'parish__website__pages__scraping',
            filter=Q(parish__website__pages__scraping__pruning__pruned_html__isnull=False)), ) \
        .order_by('-nb_page_with_confessions').distinct()[:MAX_CHURCHES_IN_RESULTS]

    return churches, len(churches) >= MAX_CHURCHES_IN_RESULTS


def get_churches_by_website(website: Website) -> tuple[list[Church], bool]:
    # TODO load website and latest scraping at the same time
    churches = Church.objects\
        .filter(parish__website=website,
                is_active=True,
                parish__website__is_active=True).all()[:MAX_CHURCHES_IN_RESULTS]

    return churches, len(churches) >= MAX_CHURCHES_IN_RESULTS


def get_churches_by_diocese(diocese: Diocese) -> tuple[list[Church], bool]:
    # TODO load parish and latest scraping at the same time
    churches = Church.objects\
        .filter(parish__diocese=diocese,
                is_active=True,
                parish__website__is_active=True) \
        .annotate(nb_page_with_confessions=Count(
            'parish__website__pages__scraping',
            filter=Q(parish__website__pages__scraping__pruning__pruned_html__isnull=False)), ) \
        .order_by('-nb_page_with_confessions').distinct()[:MAX_CHURCHES_IN_RESULTS]

    return churches, len(churches) >= MAX_CHURCHES_IN_RESULTS


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


def get_popup_and_color(church: Church):
    if church.parish.website.one_page_has_confessions():
        wording = _("ConfessionsExist")
        color = 'blue'
    elif not church.parish.website.has_been_crawled() \
            or not church.parish.website.all_pages_scraped():
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


def prepare_map(center, churches: List[Church], bounds) -> Tuple[Map, Dict[UUID, str]]:
    # Create Map Object
    folium_map = Map(location=center)

    # We save marker_names, they will be displayed in template and used in javascript
    church_marker_names = {}

    for church in churches:
        tootltip_text = f'{church.name}'
        popup_html, color = get_popup_and_color(church)
        marker = Marker(get_latitude_longitude(church.location),
                        tooltip=tootltip_text,
                        popup=Popup(html=popup_html, max_width=None),
                        icon=Icon(icon='cross', prefix='fa', color=color))
        church_marker_names[church.uuid] = marker.get_name()
        marker.add_to(folium_map)

    if bounds or len(churches) > 0:
        if bounds:
            min_lat, max_lat, min_long, max_long = bounds
        else:
            min_lat, max_lat, min_long, max_long = get_bounds(churches)
        folium_map.fit_bounds([[min_lat, min_long],
                               [max_lat, max_long]])

    return folium_map, church_marker_names


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
                        icon=Icon(icon=f'{i+1}', prefix='fa', color=color))
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
