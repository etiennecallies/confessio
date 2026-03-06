from django.urls import path

from . import views
urlpatterns = [
    path('moderate/oclocher_organization/<category>/<str:is_bug>/<str:diocese_slug>',
         views.moderate_oclocher_organization, name='moderate_next_oclocher_organization'),
    path('moderate/oclocher_organization/<category>/<str:is_bug>/<str:diocese_slug>/'
         '<uuid:moderation_uuid>',
         views.moderate_oclocher_organization, name='moderate_one_oclocher_organization'),
    path('moderate/oclocher_matching/<category>/<str:is_bug>/<str:diocese_slug>',
         views.moderate_oclocher_matching, name='moderate_next_oclocher_matching'),
    path('moderate/oclocher_matching/<category>/<str:is_bug>/<str:diocese_slug>/'
         '<uuid:moderation_uuid>',
         views.moderate_oclocher_matching, name='moderate_one_oclocher_matching'),
]
