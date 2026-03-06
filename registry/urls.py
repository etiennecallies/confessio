from django.urls import path

from . import views

urlpatterns = [
    # moderation
    path('moderate/website/<category>/<str:is_bug>/<str:diocese_slug>',
         views.moderate_website, name='moderate_next_website'),
    path('moderate/website/<category>/<str:is_bug>/<str:diocese_slug>/<uuid:moderation_uuid>',
         views.moderate_website, name='moderate_one_website'),
    path('moderate/parish/<category>/<str:is_bug>/<str:diocese_slug>',
         views.moderate_parish, name='moderate_next_parish'),
    path('moderate/parish/<category>/<str:is_bug>/<str:diocese_slug>/<uuid:moderation_uuid>',
         views.moderate_parish, name='moderate_one_parish'),
    path('moderate/church/<category>/<str:is_bug>/<str:diocese_slug>',
         views.moderate_church, name='moderate_next_church'),
    path('moderate/church/<category>/<str:is_bug>/<str:diocese_slug>/<uuid:moderation_uuid>',
         views.moderate_church, name='moderate_one_church'),
]
