from typing import List

from django.utils.translation import gettext as _

from home.models import Church
from folium import Map, Icon, Popup, Marker


##########
# SEARCH #
##########

def get_churches_in_box(location, zoom) -> List[Church]:
    # TODO load parish and latest scraping at the same time
    churches = Church.objects.all()

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
    elif not church.parish.has_pages() or not church.parish.all_pages_scraped():
        wording = _("NotScrapedYet")
        color = 'beige'
    elif not church.parish.one_page_has_confessions():
        wording = _("NoConfessionFound")
        color = 'black'
    else:
        raise NotImplemented

    link_wording = _("JumpBelow")
    popup_html = f"""
        <b>{church.name}</b><br>
        {wording}<br>
        <a href="#{church.parish.uuid}" target="_parent">{link_wording}</a>
    """

    return popup_html, color


def prepare_map(location, zoom, churches: List[Church]):
    # Create Map Object
    folium_map = Map(location=location, zoom_start=zoom)

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

    return folium_map, church_marker_names
