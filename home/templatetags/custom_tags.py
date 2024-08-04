from django.template.defaulttags import register

from home.models import WebsiteModeration, ChurchModeration, ParishModeration, \
    PruningModeration


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def negate(value):
    return not value


@register.simple_tag
def get_moderation_stats():
    return sum([
        WebsiteModeration.get_stats_by_category(),
        ParishModeration.get_stats_by_category(),
        ChurchModeration.get_stats_by_category(),
        PruningModeration.get_stats_by_category(),
    ], [])
