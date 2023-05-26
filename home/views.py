from django.shortcuts import render

from home.services.map_service import get_churches_in_box, prepare_map


def index(request):
    location = [48.859, 2.342]
    zoom = 13

    # Load parishes
    churches = get_churches_in_box(location, zoom)

    folium_map, church_marker_names = prepare_map(location, zoom, churches)

    # Get HTML Representation of Map Object
    map_html = folium_map._repr_html_()

    # Hack: we add an id to iframe of map since we need to get the element in javascript
    map_html = map_html.replace('<iframe srcdoc=', '<iframe id="map-iframe" srcdoc=')

    # We get all parishes and their churches
    parishes_by_uuid = {}
    parish_churches = {}
    for church in churches:
        parishes_by_uuid[church.parish.uuid] = church.parish
        parish_churches.setdefault(church.parish.uuid, []).append(church)

    context = {
        'map_html': map_html,
        'church_marker_names': church_marker_names,
        'parishes': parishes_by_uuid.values(),
        'parish_churches': parish_churches,
    }

    # Page from the theme 
    return render(request, 'pages/index.html', context)
