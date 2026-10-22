from django.urls import path

from . import views

urlpatterns = [
    path('moderate/file_note/<category>/<str:status>',
         views.moderate_file_note, name='moderate_next_file_note'),
    path('moderate/file_note/<category>/<str:status>/<uuid:moderation_uuid>',
         views.moderate_file_note, name='moderate_one_file_note'),
]
