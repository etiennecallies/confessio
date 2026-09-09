from django.urls import path

from . import views

urlpatterns = [
    path('moderate/crawling/<category>/<str:status>',
         views.moderate_crawling, name='moderate_next_crawling'),
    path('moderate/crawling/<category>/<str:status>/<uuid:moderation_uuid>',
         views.moderate_crawling, name='moderate_one_crawling'),

    # moderation actions
    path('moderate/recrawl_website/<uuid:website_uuid>',
         views.trigger_recrawl_for_website, name='trigger_recrawl'),
]
