from uuid import UUID

from home.models import Church
from home.services.search_service import get_churches_in_box, MAX_CHURCHES_IN_RESULTS, \
    get_count_per_diocese, TimeFilter, get_count_per_municipality, get_count_per_parish, \
    get_churches_in_area, get_churches_around, get_popular_churches, AggregationItem, \
    DEFAULT_SEARCH_BOX
from scheduling.models import IndexEvent


def get_search_results(
        latitude: float | None,
        longitude: float | None,
        min_lat: float | None,
        min_lng: float | None,
        max_lat: float | None,
        max_lng: float | None,
        time_filter: TimeFilter,
) -> tuple[list[IndexEvent], list[Church], dict[UUID, bool], list[AggregationItem]]:
    if min_lat and min_lng and max_lat and max_lng:
        index_events, churches, _, events_truncated_by_website_uuid = \
            get_churches_in_box(min_lat, max_lat, min_lng, max_lng, time_filter)
        if len(churches) == MAX_CHURCHES_IN_RESULTS:
            diocese_count = len(set(church.parish.diocese for church in churches))
            if diocese_count >= 5:
                # Search in big box, count by diocese
                aggregations = get_count_per_diocese(min_lat, max_lat, min_lng, max_lng,
                                                     time_filter)
            else:
                municipality_count = len(set((church.city, church.zipcode) for church in churches))
                parish_count = len(set(church.parish.uuid for church in churches))

                if parish_count > municipality_count:
                    # Search in big cities, many parishes, few municipalities
                    aggregations = get_count_per_municipality(min_lat, max_lat, min_lng, max_lng,
                                                              time_filter)
                else:
                    # Search in countryside, many municipalities, few parishes
                    aggregations = get_count_per_parish(min_lat, max_lat, min_lng, max_lng,
                                                        time_filter)

            singleton_aggregations = list(filter(lambda a: a.church_count == 1, aggregations))
            index_events, churches, _, events_truncated_by_website_uuid = \
                get_churches_in_area(singleton_aggregations, time_filter)
            aggregations = list(filter(lambda a: a.church_count > 1, aggregations))
        else:
            aggregations = []
    elif latitude and longitude:
        center = [latitude, longitude]
        index_events, churches, _, events_truncated_by_website_uuid = \
            get_churches_around(center, time_filter)
        aggregations = []
    else:
        min_lat, max_lat, min_lng, max_lng = DEFAULT_SEARCH_BOX
        index_events, churches, _, events_truncated_by_website_uuid = \
            get_popular_churches(min_lat, max_lat, min_lng, max_lng, time_filter)
        aggregations = []

    return index_events, churches, events_truncated_by_website_uuid, aggregations
