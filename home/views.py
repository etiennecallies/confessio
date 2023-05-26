import folium
from django.shortcuts import render
from folium import Icon, Popup

from home.models import Parish
from home.services.map_service import get_popup_and_color, get_latitude_longitude


def index(request):
    location = [48.859, 2.342]
    zoom = 13

    # Load parishes
    # TODO load parish and latest scraping at the same time
    parishes = Parish.objects.all()

    # Create Map Object
    folium_map = folium.Map(location=location, zoom_start=zoom)

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
