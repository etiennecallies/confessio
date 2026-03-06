from django.urls import path

from . import views


urlpatterns = [
    # edit
    path('edit/pruning/v1/<uuid:pruning_uuid>', views.edit_pruning_v1, name='edit_pruning_v1'),
    path('edit/pruning/human/<uuid:pruning_uuid>', views.edit_pruning_human,
         name='edit_pruning_human'),
    path('edit/pruning/v2/<uuid:pruning_uuid>', views.edit_pruning_v2, name='edit_pruning_v2'),
    path('edit/parsing/<uuid:parsing_uuid>', views.edit_parsing, name='edit_parsing'),

    # moderations
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
    path('moderate/scheduling/<category>/<str:is_bug>/<str:diocese_slug>',
         views.moderate_scheduling, name='moderate_next_scheduling'),
    path('moderate/scheduling/<category>/<str:is_bug>/<str:diocese_slug>/<uuid:moderation_uuid>',
         views.moderate_scheduling, name='moderate_one_scheduling'),

    # moderation actions
    path('moderate/erase_human_by_llm/<uuid:parsing_moderation_uuid>',
         views.moderate_erase_human_by_llm, name='moderate_erase_human_by_llm'),
    path('moderate/set_v2_as_human/<uuid:pruning_moderation_uuid>',
         views.moderate_set_v2_indices_as_human_by, name='set_v2_as_human'),

]
