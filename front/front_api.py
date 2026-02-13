from datetime import datetime, date
from enum import Enum
from typing import Literal
from uuid import UUID

from django.http import Http404
from ninja import NinjaAPI, Schema

from front.services.card.report_service import get_count_and_label
from front.services.card.website_events_service import get_website_events, ChurchEvent, \
    WebsiteEvents
from front.services.card.website_schedules_service import get_website_schedules
from front.services.search.aggregation_service import get_search_results
from front.services.search.autocomplete_service import get_aggregated_response, AutocompleteResult
from front.services.search.search_service import TimeFilter, AggregationItem, BoundingBox, \
    get_dioceses_bounding_box
from registry.models import Church, Website, Diocese
from scheduling.public_service import scheduling_get_indexed_scheduling
from scheduling.workflows.merging.sourced_schedules import SourcedScheduleItem
from scheduling.workflows.merging.sources import BaseSource, ParsingSource, OClocherSource

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
    def from_church(cls, church: Church) -> 'ChurchOut':
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


class SourceTypeEnum(str, Enum):
    PARSING = 'parsing'
    OCLOCHER = 'oclocher'


class SourceOut(Schema):
    source_type: SourceTypeEnum
    parsing_uuid: UUID | None

    @classmethod
    def from_source(cls, source: BaseSource) -> 'SourceOut':
        if isinstance(source, ParsingSource):
            return cls(
                source_type=SourceTypeEnum.PARSING,
                parsing_uuid=source.parsing_uuid,
            )
        if isinstance(source, OClocherSource):
            return cls(
                source_type=SourceTypeEnum.OCLOCHER,
                parsing_uuid=None,
            )

        raise ValueError(f'Unknown source type: {type(source)}')


class ScheduleOut(Schema):
    explanation: str
    sources: list[SourceOut]

    @classmethod
    def from_sourced_schedule_item(cls,
                                   sourced_schedule_item: SourcedScheduleItem) -> 'ScheduleOut':
        return cls(
            explanation=sourced_schedule_item.explanation,
            sources=[SourceOut.from_source(source) for source in sourced_schedule_item.sources],
        )


class ChurchDetails(ChurchOut):
    schedules: list[ScheduleOut]

    @classmethod
    def from_church_and_schedules(cls, church: Church, schedules: list[ScheduleOut]
                                  ) -> 'ChurchDetails':
        base = ChurchOut.from_church(church)

        return cls(
            **base.dict(),
            schedules=schedules
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
    min_latitude: float
    max_latitude: float
    min_longitude: float
    max_longitude: float

    @classmethod
    def from_aggregation(cls, aggregation: AggregationItem):
        return cls(
            type=aggregation.type,
            name=aggregation.name,
            church_count=aggregation.church_count,
            centroid_latitude=aggregation.centroid_latitude,
            centroid_longitude=aggregation.centroid_longitude,
            min_latitude=aggregation.min_latitude,
            max_latitude=aggregation.max_latitude,
            min_longitude=aggregation.min_longitude,
            max_longitude=aggregation.max_longitude,
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


class DioceseOut(Schema):
    uuid: UUID
    name: str
    slug: str
    min_latitude: float
    max_latitude: float
    min_longitude: float
    max_longitude: float

    @classmethod
    def from_diocese_and_box(cls, diocese: Diocese, bounding_box: BoundingBox) -> 'DioceseOut':
        return cls(
            uuid=diocese.uuid,
            name=diocese.name,
            slug=diocese.slug,
            min_latitude=bounding_box.min_latitude,
            max_latitude=bounding_box.max_latitude,
            min_longitude=bounding_box.min_longitude,
            max_longitude=bounding_box.max_longitude,
        )


class ErrorSchema(Schema):
    detail: str


#############
# ENDPOINTS #
#############

@api.get("/search", response=SearchResult)
def api_front_search(request,
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

    index_events, churches, events_truncated_by_website_uuid, aggregations = \
        get_search_results(latitude, longitude, min_lat, min_lng, max_lat, max_lng, time_filter)

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
def api_front_autocomplete(request, query: str = '') -> list[AutocompleteItem]:
    results = get_aggregated_response(query)
    return list(map(lambda r: AutocompleteItem.from_autocomplete_result(r), results))


@api.get("/church/{church_uuid}", response={200: ChurchDetails, 404: ErrorSchema})
def api_front_church_details(request, church_uuid: UUID) -> ChurchDetails:
    try:
        church = Church.objects.get(uuid=church_uuid)
    except Church.DoesNotExist:
        raise Http404(f'Church with uuid {church_uuid} not found')

    website = church.parish.website
    scheduling = scheduling_get_indexed_scheduling(website)

    website_schedules = get_website_schedules(website, [church], scheduling,
                                              only_real_churches=True)
    schedules = [ScheduleOut.from_sourced_schedule_item(ssi)
                 for ssc in website_schedules.sourced_schedules_list.sourced_schedules_of_churches
                 for ssi in ssc.sourced_schedules]
    return ChurchDetails.from_church_and_schedules(church, schedules)


@api.get("/dioceses", response={200: list[DioceseOut], 404: ErrorSchema})
def api_front_get_dioceses(request) -> list[DioceseOut]:
    dioceses_and_box = get_dioceses_bounding_box()
    return [DioceseOut.from_diocese_and_box(diocese, bounding_box)
            for diocese, bounding_box in dioceses_and_box]
