from django.urls import path

from . import views
from .api import api
from .front_api import api as front_api
from django.contrib.auth import views as auth_views

from .views import themepixel_views

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

    # Authentication
    path('accounts/login/', themepixel_views.UserLoginView.as_view(), name='login'),
    path('accounts/logout/', themepixel_views.logout_view, name='logout'),
    # path('accounts/register/', themepixel_views.register, name='register'),
    path('accounts/password-change/', themepixel_views.UserPasswordChangeView.as_view(),
         name='password_change'),
    path('accounts/password-change-done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='accounts/password_change_done.html'
    ), name='password_change_done'),
    path('accounts/password-reset/', themepixel_views.UserPasswordResetView.as_view(),
         name='password_reset'),
    path('accounts/password-reset-done/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_done.html'
    ), name='password_reset_done'),
    path('accounts/password-reset-confirm/<uidb64>/<token>/',
         themepixel_views.UserPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('accounts/password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html'
    ), name='password_reset_complete'),

    # edit
    path('edit/pruning/v1/<uuid:pruning_uuid>', views.edit_pruning_v1, name='edit_pruning_v1'),
    path('edit/pruning/human/<uuid:pruning_uuid>', views.edit_pruning_human,
         name='edit_pruning_human'),
    path('edit/pruning/v2/<uuid:pruning_uuid>', views.edit_pruning_v2, name='edit_pruning_v2'),
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
    path('moderate/crawling/<category>/<str:is_bug>/<str:diocese_slug>',
         views.moderate_crawling, name='moderate_next_crawling'),
    path('moderate/crawling/<category>/<str:is_bug>/<str:diocese_slug>/<uuid:moderation_uuid>',
         views.moderate_crawling, name='moderate_one_crawling'),
    path('moderate/scheduling/<category>/<str:is_bug>/<str:diocese_slug>',
         views.moderate_scheduling, name='moderate_next_scheduling'),
    path('moderate/scheduling/<category>/<str:is_bug>/<str:diocese_slug>/<uuid:moderation_uuid>',
         views.moderate_scheduling, name='moderate_one_scheduling'),
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

    # moderation actions
    path('moderate/merge_websites/<uuid:website_moderation_uuid>',
         views.moderate_merge_websites, name='moderate_merge_websites'),
    path('moderate/erase_human_by_llm/<uuid:parsing_moderation_uuid>',
         views.moderate_erase_human_by_llm, name='moderate_erase_human_by_llm'),
    path('moderate/set_v2_as_human/<uuid:pruning_moderation_uuid>',
         views.moderate_set_v2_indices_as_human_by, name='set_v2_as_human'),

    # contact
    path('contact', views.contact, name='contact'),
    path('contact/<message>', views.contact, name='contact_success'),
    path('contact/<message>/<email>/<path:name_text>/<path:message_text>', views.contact,
         name='contact_failure'),
    path('about', views.about, name='about'),

    # api
    path("api/", api.urls),
    path("front/api/", front_api.urls),
]
