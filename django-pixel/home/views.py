from django.shortcuts import render
from django.http import HttpResponse
import folium

# Create your views here.

def index(request):

    # Create Map Object
    m = folium.Map(location=[48.859, 2.342], zoom_start=13)

    folium.Marker([48.85, 2.35], tooltip='Click for more', popup='FR').add_to(m)
    # Get HTML Representation of Map Object
    m = m._repr_html_()
    context = {
        'm': m,
    }

    # Page from the theme 
    return render(request, 'pages/index.html', context)
