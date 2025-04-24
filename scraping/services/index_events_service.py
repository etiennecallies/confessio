from django.utils.timezone import make_aware

from home.models import Website
from home.models.index_models import WebsiteIndexEvent
from home.services.events_service import get_merged_church_schedules_list


def index_events_for_website(website: Website):
    website_churches = []
    for parish in website.parishes.all():
        for church in parish.churches.all():
            website_churches.append(church)

    merged_church_schedules_list = get_merged_church_schedules_list(
        website, website_churches, day_filter=None, max_days=10
    )

    website_index_to_add = []

    for church_events in merged_church_schedules_list.church_events_by_day.values():
        for church_event in church_events:
            website_index_event = WebsiteIndexEvent(
                church=church_event.church,
                website=website,
                start=make_aware(church_event.event.start),
                end=make_aware(church_event.event.end) if church_event.event.end else None,
                is_explicitely_other=church_event.is_church_explicitly_other,
            )
            website_index_to_add.append(website_index_event)

    # Remove existing events
    WebsiteIndexEvent.objects.filter(website=website).delete()

    for website_index_event in website_index_to_add:
        website_index_event.save()
