from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('qualify-page/<uuid:page_uuid>', views.qualify_page, name='qualify_page'),
    path('contact', views.contact, name='contact'),
]
