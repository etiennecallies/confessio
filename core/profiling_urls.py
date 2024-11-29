"""URL Configuration for profiling."""
from django.urls import include, path

from core.urls import urlpatterns

urlpatterns = [path('silk/', include('silk.urls', namespace='silk'))] + urlpatterns
