from datetime import datetime, date
from uuid import UUID

from ninja import NinjaAPI, Schema, Field

from home.models import Church, Website
from home.services.autocomplete_service import get_aggregated_response, AutocompleteResult
from home.services.report_service import get_count_and_label
from home.services.search_service import TimeFilter, get_churches_in_box, \
    get_churches_around, get_popular_churches
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
    reports_count: list[dict]

    @classmethod
    def from_website(cls,
                     website: Website,
                     events: WebsiteEvents,
                     reports_count: list[dict]):
        return cls(
            uuid=website.uuid,
            name=website.name,
            events=[EventOut.from_church_event(event)
                    for events in events.church_events_by_day.values()
                    for event in events],
            reports_count=reports_count,
        )


class SearchResult(Schema):
    churches: list[ChurchOut]
    websites: list[WebsiteOut]
    has_more_results: bool = Field(
        description="whether the result was truncated due to too many results"
    )

    @classmethod
    def from_result(cls,
                    churches: list[Church],
                    websites: list[Website],
                    events_by_website: dict[UUID, WebsiteEvents],
                    reports_count_by_website: dict[UUID, list[dict]],
                    has_more_results: bool):
        churches = [ChurchOut.from_church(church) for church in churches]
        websites_out = []
        for website in websites:
            events = events_by_website.get(website.uuid, [])
            reports_count = reports_count_by_website.get(website.uuid, [])
            websites_out.append(
                WebsiteOut.from_website(website, events, reports_count)
            )

        return cls(
            churches=churches,
            websites=websites_out,
            has_more_results=has_more_results,
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
        index_events, churches, has_more_results, events_truncated_by_website_uuid = \
            get_churches_in_box(min_lat, max_lat, min_lng, max_lng, time_filter)

    elif latitude and longitude:
        center = [latitude, longitude]
        index_events, churches, _, events_truncated_by_website_uuid = \
            get_churches_around(center, time_filter)
        has_more_results = False
    else:
        index_events, churches, has_more_results, events_truncated_by_website_uuid = \
            get_popular_churches(time_filter)
        if time_filter.is_null():
            has_more_results = False

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
        churches, websites, events_by_website,
        reports_count_by_website, has_more_results
    )


@api.get("/autocomplete", response=list[AutocompleteItem])
def autocomplete(request, query: str = '') -> list[AutocompleteItem]:
    results = get_aggregated_response(query)
    return list(map(lambda r: AutocompleteItem.from_autocomplete_result(r), results))
