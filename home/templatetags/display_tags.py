from django.template.defaulttags import register
from django.template.loader import render_to_string

from home.models import Parish, Church, Website


@register.simple_tag
def display_website(website: Website):
    return render_to_string('partials/website_display.html', {'website': website})


@register.simple_tag
def display_parish(parish: Parish):
    return render_to_string('partials/parish_display.html', {'parish': parish})


@register.simple_tag
def display_church(church: Church):
    return render_to_string('partials/church_display.html', {'church': church})
