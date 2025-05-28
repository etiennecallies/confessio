from django.urls import path

from .api import api

urlpatterns = [
    # api
    path("api/", api.urls),
]
