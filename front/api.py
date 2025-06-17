from datetime import datetime, date
from typing import Literal
from uuid import UUID

from ninja import NinjaAPI, Schema

from home.models import Church, Website
from home.services.autocomplete_service import get_aggregated_response, AutocompleteResult
from home.services.report_service import get_count_and_label
from home.services.search_service import TimeFilter, get_churches_in_box, \
    get_churches_around, get_popular_churches, get_count_per_diocese, get_count_per_municipality, \
    get_count_per_parish, get_churches_in_area, AggregationItem, MAX_CHURCHES_IN_RESULTS
from home.services.website_events_service import get_website_events, ChurchEvent, WebsiteEvents

api = NinjaAPI(urls_namespace='front_api')


##########
# MODELS #
##########

class ChurchOut(Schema):
    uuid: UUID
    name: str
    latitude: float
    longitude: float
    address: str | None
    zipcode: str | None
    city: str | None
    website_uuid: UUID

    @classmethod
    def from_church(cls, church: Church):
        return cls(
            uuid=church.uuid,
            name=church.name,
            latitude=church.location.y,
            longitude=church.location.x,
            address=church.address,
            zipcode=church.zipcode,
            city=church.city,
            website_uuid=church.parish.website_id,
        )


class EventOut(Schema):
    church_uuid: UUID | None
    is_church_explicitly_other: bool
    start: datetime
    end: datetime | None
    source_has_been_moderated: bool

    @classmethod
    def from_church_event(cls, church_event: ChurchEvent):
        return cls(
            church_uuid=church_event.church.uuid if church_event.church else None,
            is_church_explicitly_other=church_event.is_church_explicitly_other,
            start=church_event.start,
            end=church_event.end,
            source_has_been_moderated=church_event.has_been_moderated,
        )


class WebsiteOut(Schema):
    uuid: UUID
    name: str
    events: list[EventOut]
    has_more_events: bool
    reports_count: list[dict]

    @classmethod
    def from_website(cls,
                     website: Website,
                     events: WebsiteEvents,
                     has_more_events: bool,
                     reports_count: list[dict]):
        return cls(
            uuid=website.uuid,
            name=website.name,
            events=[EventOut.from_church_event(event)
                    for events in events.church_events_by_day.values()
                    for event in events],
            has_more_events=has_more_events,
            reports_count=reports_count,
        )


class AggregationOut(Schema):
    type: Literal['diocese', 'parish', 'municipality']
    name: str
    church_count: int
    centroid_latitude: float
    centroid_longitude: float

    @classmethod
    def from_aggregation(cls, aggregation: AggregationItem):
        return cls(
            type=aggregation.type,
            name=aggregation.name,
            church_count=aggregation.church_count,
            centroid_latitude=aggregation.centroid_latitude,
            centroid_longitude=aggregation.centroid_longitude,
        )


class SearchResult(Schema):
    churches: list[ChurchOut]
    websites: list[WebsiteOut]
    aggregations: list[AggregationOut]

    @classmethod
    def from_result(cls,
                    churches: list[Church],
                    websites: list[Website],
                    events_by_website: dict[UUID, WebsiteEvents],
                    events_truncated_by_website_uuid: dict[UUID, bool],
                    reports_count_by_website: dict[UUID, list[dict]],
                    aggregation_items: list[AggregationItem]):
        churches = [ChurchOut.from_church(church) for church in churches]
        websites_out = []
        for website in websites:
            events = events_by_website.get(website.uuid, [])
            events_truncated = events_truncated_by_website_uuid.get(website.uuid, False)
            reports_count = reports_count_by_website.get(website.uuid, [])
            websites_out.append(
                WebsiteOut.from_website(website, events, events_truncated, reports_count)
            )
        aggregations = [AggregationOut.from_aggregation(aggregation)
                        for aggregation in aggregation_items]

        return cls(
            churches=churches,
            websites=websites_out,
            aggregations=aggregations,
        )


class AutocompleteItem(Schema):
    type: str
    name: str
    context: str | None
    url: str
    latitude: float | None = None
    longitude: float | None = None

    @classmethod
    def from_autocomplete_result(cls, result: AutocompleteResult):
        return cls(
            type=result.type,
            name=result.name,
            context=result.context,
            url=result.url,
            latitude=result.latitude,
            longitude=result.longitude,
        )


#############
# ENDPOINTS #
#############

@api.get("/search", response=SearchResult)
def api_search(request,
               latitude: float | None = None,
               longitude: float | None = None,
               min_lat: float | None = None,
               min_lng: float | None = None,
               max_lat: float | None = None,
               max_lng: float | None = None,
               date_filter: date | None = None,
               hour_min: int = 0, hour_max: int = 24 * 60 - 1
               ) -> SearchResult:
    time_filter = TimeFilter(
        day_filter=date_filter,
        hour_min=hour_min,
        hour_max=hour_max,
    )

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
        index_events, churches, _, events_truncated_by_website_uuid = \
            get_popular_churches(time_filter)
        aggregations = []

    # We get all websites and their churches
    websites_by_uuid = {}
    website_churches = {}
    for church in churches:
        websites_by_uuid[church.parish.website.uuid] = church.parish.website
        website_churches.setdefault(church.parish.website.uuid, []).append(church)
    websites = list(websites_by_uuid.values())

    index_events_by_website = {}
    for index_event in index_events:
        index_events_by_website.setdefault(index_event.church.parish.website.uuid, []) \
            .append(index_event)

    events_by_website = {}
    for website in websites:
        events_by_website[website.uuid] = get_website_events(
            index_events_by_website.get(website.uuid, []),
            events_truncated_by_website_uuid[website.uuid],
            time_filter.day_filter is not None
        )

    # Count reports for each website
    reports_count_by_website = {}
    for website in websites:
        reports_count_by_website[website.uuid] = get_count_and_label(website)

    # TODO add search hit
    # new_search_hit(request, len(websites))

    return SearchResult.from_result(
        churches, websites, events_by_website, events_truncated_by_website_uuid,
        reports_count_by_website, aggregations
    )


@api.get("/autocomplete", response=list[AutocompleteItem])
def autocomplete(request, query: str = '') -> list[AutocompleteItem]:
    results = get_aggregated_response(query)
    return list(map(lambda r: AutocompleteItem.from_autocomplete_result(r), results))
