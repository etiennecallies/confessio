from django.urls import path

from . import views

urlpatterns = [
    # index
    path('', views.index, name='index'),
    path('autocomplete', views.autocomplete, name='autocomplete'),
    path('dioceses', views.dioceses_list, name='dioceses_list'),
    path('diocese/<str:diocese_slug>', views.index, name='diocese_view'),

    # report
    path('report/<uuid:website_uuid>', views.report, name='report'),

    # edit
    path('edit/pruning/<uuid:pruning_uuid>', views.edit_pruning, name='edit_pruning'),
    path('edit/parsing/<uuid:parsing_uuid>', views.edit_parsing, name='edit_parsing'),

    # moderation
    path('moderate/website/<category>/<str:is_bug>',
         views.moderate_website, name='moderate_next_website'),
    path('moderate/website/<category>/<str:is_bug>/<uuid:moderation_uuid>',
         views.moderate_website, name='moderate_one_website'),
    path('moderate/parish/<category>/<str:is_bug>',
         views.moderate_parish, name='moderate_next_parish'),
    path('moderate/parish/<category>/<str:is_bug>/<uuid:moderation_uuid>',
         views.moderate_parish, name='moderate_one_parish'),
    path('moderate/church/<category>/<str:is_bug>',
         views.moderate_church, name='moderate_next_church'),
    path('moderate/church/<category>/<str:is_bug>/<uuid:moderation_uuid>',
         views.moderate_church, name='moderate_one_church'),
    path('moderate/pruning/<category>/<str:is_bug>',
         views.moderate_pruning, name='moderate_next_pruning'),
    path('moderate/pruning/<category>/<str:is_bug>/<uuid:moderation_uuid>',
         views.moderate_pruning, name='moderate_one_pruning'),
    path('moderate/sentence/<category>/<str:is_bug>',
         views.moderate_sentence, name='moderate_next_sentence'),
    path('moderate/sentence/<category>/<str:is_bug>/<uuid:moderation_uuid>',
         views.moderate_sentence, name='moderate_one_sentence'),
    path('moderate/parsing/<category>/<str:is_bug>',
         views.moderate_parsing, name='moderate_next_parsing'),
    path('moderate/parsing/<category>/<str:is_bug>/<uuid:moderation_uuid>',
         views.moderate_parsing, name='moderate_one_parsing'),
    path('moderate/merge_websites/<uuid:website_moderation_uuid>',
         views.moderate_merge_websites, name='moderate_merge_websites'),
    path('moderate/erase_human_by_llm/<uuid:parsing_moderation_uuid>',
         views.moderate_erase_human_by_llm, name='moderate_erase_human_by_llm'),

    # contact
    path('contact', views.contact, name='contact'),
    path('contact/<message>', views.contact, name='contact_success'),
    path('contact/<message>/<name>/<email>/<path:message_text>', views.contact,
         name='contact_failure'),
]
