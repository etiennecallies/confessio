import folium
from django.shortcuts import render
from folium import Icon, Popup

from home.models import Parish
from django.utils.translation import gettext as _


# Create your views here.

def get_latitude_longitude(point):
    return [point.coords[1], point.coords[0]]


def get_popup_and_color(parish: Parish, church):
    if parish.has_confessions():
        wording = _("ConfessionsExist")
        color = 'blue'
    elif parish.not_scraped_yet() or not parish.has_pages():
        wording = _("NotScrapedYet")
        color = 'beige'
    elif not parish.has_confessions():
        wording = _("NoConfessionFound")
        color = 'black'
    else:
        raise NotImplemented

    link_wording = _("JumpBelow")
    popup_html = f"""
        <b>{church.name}</b><br>
        {wording}<br>
        <a href="#{parish.uuid}" target="_parent">{link_wording}</a>
    """

    return popup_html, color


def index(request):

    # Load parishes
    # TODO load parish and latest scraping at the same time
    parishes = Parish.objects.all()

    # Create Map Object
    folium_map = folium.Map(location=[48.859, 2.342], zoom_start=13)

    # We save marker_names, they will be displayed in template and used in javascript
    church_marker_names = {}

    for parish in parishes:
        for church in parish.churches.all():
            tootltip_text = f'{church.name}'
            popup_html, color = get_popup_and_color(parish, church)
            marker = folium.Marker(get_latitude_longitude(church.location), tooltip=tootltip_text,
                                   popup=Popup(html=popup_html, max_width=None),
                                   icon=Icon(icon='cross', prefix='fa', color=color))
            church_marker_names[church.uuid] = marker.get_name()
            marker.add_to(folium_map)

    # Get HTML Representation of Map Object
    map_html = folium_map._repr_html_()

    # Hack: we add an id to iframe of map since we need to get the element in javascript
    map_html = map_html.replace('<iframe srcdoc=', '<iframe id="map-iframe" srcdoc=')

    context = {
        'map_html': map_html,
        'parishes': parishes,
        'church_marker_names': church_marker_names
    }

    # Page from the theme 
    return render(request, 'pages/index.html', context)
