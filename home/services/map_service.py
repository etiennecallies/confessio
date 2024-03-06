from typing import List, Tuple, Dict
from uuid import UUID

from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point, Polygon
from django.contrib.gis.measure import D
from django.utils.translation import gettext as _

from home.models import Church
from folium import Map, Icon, Popup, Marker


MAX_CHURCHES_IN_RESULTS = 50


##########
# SEARCH #
##########

def get_churches_around(center) -> List[Church]:
    latitude, longitude = center
    center_as_point = Point(x=longitude, y=latitude)

    # TODO load parish and latest scraping at the same time
    churches = Church.objects\
        .filter(location__dwithin=(center_as_point, D(km=5)), parish__is_active=True) \
        .annotate(distance=Distance('location', center_as_point)) \
        .order_by('distance')[:MAX_CHURCHES_IN_RESULTS]

    return churches


def get_churches_in_box(min_lat, max_lat, min_long, max_long) -> List[Church]:
    polygon = Polygon.from_bbox((min_long, min_lat, max_long, max_lat))

    # TODO load parish and latest scraping at the same time
    churches = Church.objects\
        .filter(location__within=polygon, parish__is_active=True).all()[:MAX_CHURCHES_IN_RESULTS]

    return churches


###########
# DISPLAY #
###########

def get_latitude_longitude(point):
    return [point.coords[1], point.coords[0]]


def get_popup_and_color(church: Church):
    if church.parish.one_page_has_confessions():
        wording = _("ConfessionsExist")
        color = 'blue'
    elif not church.parish.has_been_crawled() \
            or not church.parish.all_pages_scraped() \
            or not church.parish.all_pages_pruned():
        wording = _("NotCrawledYet")
        color = 'beige'
    else:
        wording = _("NoConfessionFound")
        color = 'black'

    link_wording = _("JumpBelow")
    popup_html = f"""
        <b>{church.name}</b><br>
        {wording}<br>
        <a href="#{church.parish.uuid}" target="_parent">{link_wording}</a>
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

    if bounds:
        min_lat, max_lat, min_long, max_long = bounds
        folium_map.fit_bounds([[min_lat, min_long],
                               [max_lat, max_long]])
    elif len(churches) > 0:
        latitudes = list(map(lambda c: c.location.y, churches))
        longitudes = list(map(lambda c: c.location.x, churches))
        folium_map.fit_bounds([[min(latitudes), min(longitudes)],
                               [max(latitudes), max(longitudes)]])

    return folium_map, church_marker_names
