from django.shortcuts import render
from django.http import HttpResponse
import folium

from home.models import Parish


# Create your views here.

def get_latitude_longitude(point):
    return [point.coords[1], point.coords[0]]


def index(request):

    # Load parishes
    # TODO load parish and last scrappings at the same time
    parishes = Parish.objects.all()

    # Create Map Object
    m = folium.Map(location=[48.859, 2.342], zoom_start=13)

    for parish in parishes:
        for church in parish.churches.all():
            popup_content = f'{church.name}'
            folium.Marker(get_latitude_longitude(church.location),
                          tooltip='Click for more',
                          popup=popup_content,
                          ).add_to(m)

    # Get HTML Representation of Map Object
    map_html = m._repr_html_()
    print(map_html)

    context = {
        'map_html': map_html,
        'parishes': parishes
    }

    # Page from the theme 
    return render(request, 'pages/index.html', context)
