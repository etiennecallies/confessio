from django.template.defaulttags import register

from home.models import WebsiteModeration, ChurchModeration, ScrapingModeration


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.simple_tag
def get_moderation_stats():
    return sum([
        WebsiteModeration.get_stats_by_category(),
        ChurchModeration.get_stats_by_category(),
        ScrapingModeration.get_stats_by_category(),
    ], [])
