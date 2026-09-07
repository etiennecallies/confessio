from django.urls import path

from . import views

urlpatterns = [
    path('moderate/image/<category>/<str:status>/<str:diocese_slug>',
         views.moderate_image, name='moderate_next_image'),
    path('moderate/image/<category>/<str:status>/<str:diocese_slug>/<uuid:moderation_uuid>',
         views.moderate_image, name='moderate_one_image'),
]
