from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('qualify-page/<uuid:page_uuid>', views.qualify_page, name='qualify_page'),
    path('moderate-parish/<category>', views.moderate_parish, name='moderate_next_parish'),
    path('moderate-parish/<category>/<uuid:moderation_uuid>', views.moderate_parish,
         name='moderate_one_parish'),
    path('moderate-church/<category>', views.moderate_church, name='moderate_next_church'),
    path('moderate-church/<category>/<uuid:moderation_uuid>', views.moderate_church,
         name='moderate_one_church'),
    path('moderate-scraping/<category>', views.moderate_scraping, name='moderate_next_scraping'),
    path('moderate-scraping/<category>/<uuid:moderation_uuid>', views.moderate_scraping,
         name='moderate_one_scraping'),
    path('contact', views.contact, name='contact'),
    path('contact/<message>', views.contact, name='contact_with_message'),
]
