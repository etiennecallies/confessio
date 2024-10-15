from django.contrib.gis.geos import Point
from django.template.defaulttags import register
from django.template.loader import render_to_string

from home.models import Parish, Church, Website, Pruning
from home.services.map_service import (get_map_with_single_location,
                                       get_map_with_multiple_locations,
                                       get_map_with_alternative_locations)
from scraping.parse.schedules import SchedulesList, Event
from home.utils.list_utils import group_consecutive_indices


@register.simple_tag
def display_website(website: Website):
    return render_to_string('partials/website_display.html', {'website': website})


@register.simple_tag
def display_parish(parish: Parish):
    return render_to_string('partials/parish_display.html', {'parish': parish})


@register.simple_tag
def display_church(church: Church, with_map=True):
    return render_to_string('partials/church_display.html', {
        'church': church,
        'with_map': with_map,
    })


@register.simple_tag
def display_event(event: Event):
    return render_to_string('partials/event_display.html', {'event': event})


@register.simple_tag
def display_bool(v: bool):
    return render_to_string('partials/bool_display.html', {'v': v})


@register.simple_tag
def display_location(location: Point):
    folimum_map = get_map_with_single_location(location)
    map_html = folimum_map._repr_html_()

    return render_to_string('partials/location_display.html', {'map_html': map_html})


@register.simple_tag
def display_churches_location(churches: list[Church]):
    folimum_map = get_map_with_multiple_locations(churches)
    if folimum_map:
        map_html = folimum_map._repr_html_()
    else:
        map_html = '<div>No churches to display</div>'

    return render_to_string('partials/location_display.html', {'map_html': map_html})


@register.simple_tag
def display_similar_churches_location(church: Church, sorted_similar_churches: list[Church]):
    folimum_map = get_map_with_alternative_locations(church, sorted_similar_churches)
    map_html = folimum_map._repr_html_()

    return render_to_string('partials/location_display.html', {'map_html': map_html})


@register.simple_tag
def display_schedules_list(schedules_list: SchedulesList):
    return render_to_string('partials/schedules_display.html', {
        'schedules_list': schedules_list,
        'schedules_list_json': schedules_list.model_dump_json(),
    })


@register.simple_tag
def display_expandable_pruning(pruning: Pruning):
    lines = pruning.extracted_html.split('<br>\n')
    consecutive_indices = group_consecutive_indices(len(lines), pruning.pruned_indices)

    spans = []
    for is_displayed, indices in consecutive_indices:
        span_lines = lines[min(indices):max(indices) + 1]
        spans.append({
            'html': '<br>'.join(span_lines),
            'is_displayed': is_displayed
        })

    return render_to_string('partials/expandable_pruning_display.html', {
        'spans': spans,
    })
