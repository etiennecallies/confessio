from django.urls import path

from . import views
from .api import api

urlpatterns = [
    # index
    path('', views.index, name='index'),
    path('autocomplete', views.autocomplete, name='autocomplete'),
    path('website_events/<uuid:website_uuid>', views.partial_website_events,
         name='website_events'),
    path('website_churches/<uuid:website_uuid>', views.partial_website_churches,
         name='website_churches'),
    path('website_sources/<uuid:website_uuid>', views.partial_website_sources,
         name='website_sources'),
    path('dioceses', views.dioceses_list, name='dioceses_list'),
    path('diocese/<str:diocese_slug>', views.index, name='diocese_view'),
    path('around_place', views.index, name='around_place_view'),
    path('in_area', views.index, name='in_area_view'),
    path('around_me', views.index, {'is_around_me': True}, name='around_me_view'),
    path('paroisse/<uuid:website_uuid>', views.index, name='website_view'),
    path('paroisse/<uuid:website_uuid>/upload_image', views.website_upload_image,
         name='website_upload_image'),

    # edit
    path('edit/pruning/v1/<uuid:pruning_uuid>', views.edit_pruning_v1, name='edit_pruning_v1'),
    path('edit/pruning/human/<uuid:pruning_uuid>', views.edit_pruning_human,
         name='edit_pruning_human'),
    path('edit/parsing/<uuid:parsing_uuid>', views.edit_parsing, name='edit_parsing'),

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
    path('moderate/pruning/<category>/<str:is_bug>/<str:diocese_slug>',
         views.moderate_pruning, name='moderate_next_pruning'),
    path('moderate/pruning/<category>/<str:is_bug>/<str:diocese_slug>/<uuid:moderation_uuid>',
         views.moderate_pruning, name='moderate_one_pruning'),
    path('moderate/sentence/<category>/<str:is_bug>/<str:diocese_slug>',
         views.moderate_sentence, name='moderate_next_sentence'),
    path('moderate/sentence/<category>/<str:is_bug>/<str:diocese_slug>/<uuid:moderation_uuid>',
         views.moderate_sentence, name='moderate_one_sentence'),
    path('moderate/parsing/<category>/<str:is_bug>/<str:diocese_slug>',
         views.moderate_parsing, name='moderate_next_parsing'),
    path('moderate/parsing/<category>/<str:is_bug>/<str:diocese_slug>/<uuid:moderation_uuid>',
         views.moderate_parsing, name='moderate_one_parsing'),
    path('moderate/report/<category>/<str:is_bug>/<str:diocese_slug>',
         views.moderate_report, name='moderate_next_report'),
    path('moderate/report/<category>/<str:is_bug>/<str:diocese_slug>/<uuid:moderation_uuid>',
         views.moderate_report, name='moderate_one_report'),

    # moderation actions
    path('moderate/merge_websites/<uuid:website_moderation_uuid>',
         views.moderate_merge_websites, name='moderate_merge_websites'),
    path('moderate/erase_human_by_llm/<uuid:parsing_moderation_uuid>',
         views.moderate_erase_human_by_llm, name='moderate_erase_human_by_llm'),

    # contact
    path('contact', views.contact, name='contact'),
    path('contact/<message>', views.contact, name='contact_success'),
    path('contact/<message>/<email>/<path:name_text>/<path:message_text>', views.contact,
         name='contact_failure'),
    path('about', views.about, name='about'),

    # api
    path("api/", api.urls),
]
