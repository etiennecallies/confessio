from django.urls import path

from . import views

urlpatterns = [
    # index
    path('', views.index, name='index'),
    path('autocomplete', views.autocomplete, name='autocomplete'),
    path('diocese', views.diocese_list, name='diocese_list'),
    path('diocese/<str:diocese_slug>', views.diocese_view, name='diocese_view'),

    # qualify
    path('qualify/page/<uuid:page_uuid>', views.qualify_page, name='qualify_page'),

    # moderation
    path('moderate/parish/<category>/<str:is_bug>',
         views.moderate_parish, name='moderate_next_parish'),
    path('moderate/parish/<category>/<str:is_bug>/<uuid:moderation_uuid>',
         views.moderate_parish, name='moderate_one_parish'),
    path('moderate/church/<category>/<str:is_bug>',
         views.moderate_church, name='moderate_next_church'),
    path('moderate/church/<category>/<str:is_bug>/<uuid:moderation_uuid>',
         views.moderate_church, name='moderate_one_church'),
    path('moderate/scraping/<category>/<str:is_bug>',
         views.moderate_scraping, name='moderate_next_scraping'),
    path('moderate/scraping/<category>/<str:is_bug>/<uuid:moderation_uuid>',
         views.moderate_scraping, name='moderate_one_scraping'),

    # contact
    path('contact', views.contact, name='contact'),
    path('contact/<message>', views.contact, name='contact_with_message'),
]
