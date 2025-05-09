from datetime import date
from uuid import UUID

from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point, Polygon
from django.contrib.gis.measure import D
from django.db.models import QuerySet, OuterRef, Subquery, Exists, ExpressionWrapper, Q, \
    BooleanField
from pydantic import BaseModel

from home.models import Church, Website, Diocese, ChurchIndexEvent
from home.utils.date_utils import time_from_minutes

MAX_CHURCHES_IN_RESULTS = 50
MAX_WEBSITES_IN_RESULTS = 10


###########
# OBJECTS #
###########

class TimeFilter(BaseModel):
    day_filter: date | None
    hour_min: int | None
    hour_max: int | None

    def is_null(self):
        return self.day_filter is None and self.hour_min is None and self.hour_max is None


###############
# QUERY UTILS #
###############

def build_event_subquery(time_filter: TimeFilter):
    event_query = ChurchIndexEvent.objects.filter(church_id=OuterRef('pk'),
                                                  day__gte=date.today())

    if not time_filter.is_null():
        event_query = add_event_filters(event_query, time_filter)

    return event_query


def build_church_query(time_filter: TimeFilter) -> QuerySet[Church]:
    event_query = build_event_subquery(time_filter).annotate(
        located_event=ExpressionWrapper(Q(is_explicitely_other__isnull=True),
                                        output_field=BooleanField())
    ).order_by(
        '-located_event',
        'day',
        'start_time'
    ).values('uuid')

    church_query = Church.objects.select_related('parish__website') \
        .prefetch_related('parish__website__reports') \
        .annotate(next_event_uuid=Subquery(event_query[:1])) \
        .filter(is_active=True,
                parish__website__is_active=True)\
        .only("name",
              "city",
              "location",
              "parish__website__uuid",
              "parish__website__name",
              "parish__website__home_url",
              "parish__website__unreliability_reason",
              )

    if not time_filter.is_null():
        church_query = church_query.filter(next_event_uuid__isnull=False)

    return church_query


def build_events_query(church_by_uuid: dict[UUID, Church],
                       time_filter: TimeFilter) -> QuerySet[ChurchIndexEvent]:
    event_query = ChurchIndexEvent.objects \
        .filter(church__uuid__in=church_by_uuid.keys())
    event_query = add_event_filters(event_query, time_filter)

    return event_query


def add_event_filters(event_query: QuerySet[ChurchIndexEvent],
                      time_filter: TimeFilter) -> QuerySet[ChurchIndexEvent]:
    if time_filter.day_filter:
        event_query = event_query.filter(day=time_filter.day_filter)

    if time_filter.hour_min is not None or time_filter.hour_max is not None:
        hour_min = time_filter.hour_min or 0
        hour_max = time_filter.hour_max or 24 * 60 - 1
        event_query = event_query.filter(indexed_end_time__gte=time_from_minutes(hour_min),
                                         start_time__lte=time_from_minutes(hour_max))
    return event_query


def truncate_results(church_query: QuerySet[Church],
                     time_filter: TimeFilter
                     ) -> tuple[list[ChurchIndexEvent], list[Church], bool, dict[UUID, bool]]:
    churches = church_query.all()[:MAX_CHURCHES_IN_RESULTS]

    non_truncated_count = 0
    non_truncated_churches = []
    truncated_churches = []

    all_churches_have_events = True

    events_truncated_by_website_uuid = {}
    for church in churches:
        website_uuid = church.parish.website.uuid
        if website_uuid not in events_truncated_by_website_uuid:
            if non_truncated_count >= MAX_WEBSITES_IN_RESULTS:
                events_truncated_by_website_uuid[website_uuid] = True
            else:
                events_truncated_by_website_uuid[website_uuid] = False
                non_truncated_count += 1

        if events_truncated_by_website_uuid[website_uuid]:
            truncated_churches.append(church)
        else:
            non_truncated_churches.append(church)

        if church.next_event_uuid is None:
            all_churches_have_events = False

    non_truncated_church_by_uuid = {church.uuid: church for church in non_truncated_churches}
    truncated_church_by_uuid = {church.uuid: church for church in truncated_churches}
    events = fetch_events(non_truncated_church_by_uuid, time_filter) \
        + fetch_next_event(truncated_church_by_uuid)

    return (events, churches, all_churches_have_events and len(churches) == MAX_CHURCHES_IN_RESULTS,
            events_truncated_by_website_uuid)


def fetch_events(church_by_uuid: dict[UUID, Church],
                 time_filter: TimeFilter) -> list[ChurchIndexEvent]:
    events = build_events_query(church_by_uuid, time_filter).all()
    for event in events:
        event.church = church_by_uuid.get(event.church_id)

    return list(events)


def fetch_next_event(church_by_uuid: dict[UUID, Church]) -> list[ChurchIndexEvent]:
    events_uuid = [church.next_event_uuid for church in church_by_uuid.values()
                   if church.next_event_uuid]
    events = ChurchIndexEvent.objects.filter(uuid__in=events_uuid)

    for event in events:
        event.church = church_by_uuid.get(event.church_id)

    return list(events)


###########
# QUERIES #
###########

def get_churches_around(center, time_filter: TimeFilter,
                        ) -> tuple[list[ChurchIndexEvent], list[Church], bool, dict[UUID, bool]]:
    latitude, longitude = center
    center_as_point = Point(x=longitude, y=latitude)

    church_query = build_church_query(time_filter) \
        .filter(location__dwithin=(center_as_point, D(km=5))) \
        .annotate(distance=Distance('location', center_as_point)) \
        .order_by('distance')

    return truncate_results(church_query, time_filter)


def get_churches_in_box(min_lat, max_lat, min_long, max_long, time_filter: TimeFilter
                        ) -> tuple[list[ChurchIndexEvent], list[Church], bool, dict[UUID, bool]]:
    polygon = Polygon.from_bbox((min_long, min_lat, max_long, max_lat))

    church_query = build_church_query(time_filter)\
        .annotate(has_event=Exists(build_event_subquery(time_filter)))\
        .filter(location__within=polygon)\
        .order_by(
        '-has_event',
        '-parish__website__nb_recent_hits'
    )

    return truncate_results(church_query, time_filter)


def get_churches_by_website(
        website: Website,
        time_filter: TimeFilter,
) -> tuple[list[ChurchIndexEvent], list[Church], bool, dict[UUID, bool]]:
    church_query = build_church_query(time_filter)\
        .filter(parish__website=website)

    return truncate_results(church_query, time_filter)


def get_churches_by_diocese(
        diocese: Diocese,
        time_filter: TimeFilter,
) -> tuple[list[ChurchIndexEvent], list[Church], bool, dict[UUID, bool]]:
    event_query = build_event_subquery(time_filter).filter(is_explicitely_other__isnull=True)
    church_query = build_church_query(time_filter).annotate(has_located_event=Exists(event_query))\
        .filter(parish__diocese=diocese)\
        .order_by(
        '-has_located_event',
        '-parish__website__nb_recent_hits'
    )

    return truncate_results(church_query, time_filter)


def get_popular_churches(time_filter: TimeFilter,
                         ) -> tuple[list[ChurchIndexEvent], list[Church], bool, dict[UUID, bool]]:
    event_query = build_event_subquery(time_filter).filter(is_explicitely_other__isnull=True)
    church_query = build_church_query(time_filter).annotate(has_located_event=Exists(event_query))\
        .order_by(
        '-has_located_event',
        '-parish__website__is_best_diocese_hit',
        '-parish__website__nb_recent_hits',
    )

    return truncate_results(church_query, time_filter)
