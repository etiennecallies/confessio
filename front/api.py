from datetime import datetime
from uuid import UUID

from django.db.models import Exists, OuterRef
from ninja import NinjaAPI, Schema, Field

from registry.models import Church, ChurchModeration, Parish, Website

api = NinjaAPI(urls_namespace='main_api')


############
# CHURCHES #
############

class ChurchOut(Schema):
    uuid: UUID
    name: str
    latitude: float
    longitude: float
    address: str | None
    zipcode: str | None
    city: str | None
    messesinfo_id: str | None
    wikidata_id: str | None
    trouverunemesse_id: UUID | None
    trouverunemesse_slug: str | None
    parish_uuid: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    has_validated_moderation: bool = Field(
        description="whether it has been moderated by a human"
    )
    has_unvalidated_moderation: bool = Field(
        description="whether there is pending moderation for human"
    )

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
            messesinfo_id=church.messesinfo_id,
            wikidata_id=church.wikidata_id,
            trouverunemesse_id=church.trouverunemesse_id,
            trouverunemesse_slug=church.trouverunemesse_slug,
            parish_uuid=church.parish_id,
            is_active=church.is_active,
            created_at=church.created_at,
            updated_at=church.updated_at,
            has_validated_moderation=church.has_validated_moderation,
            has_unvalidated_moderation=church.has_unvalidated_moderation,
        )


@api.get("/churches", response=list[ChurchOut])
def api_public_churches(request, limit: int = 10, offset: int = 0, updated_from: datetime = None
                        ) -> list[ChurchOut]:
    limit = max(0, min(100, limit))
    offset = max(0, offset)

    church_query = Church.objects.annotate(
        has_validated_moderation=Exists(
            ChurchModeration.history.filter(church=OuterRef('pk'), history_user_id__isnull=False)
        ),
        has_unvalidated_moderation=Exists(
            ChurchModeration.objects.filter(church=OuterRef('pk'), validated_at__isnull=True)
        ),
    )
    if updated_from:
        church_query = church_query.filter(updated_at__gte=updated_from)
    churches = church_query.order_by('updated_at').all()[offset:offset + limit]

    return list(map(ChurchOut.from_church, churches))


############
# PARISHES #
############

class ParishOut(Schema):
    uuid: UUID
    name: str
    messesinfo_id: str | None
    website_uuid: UUID | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_parish(cls, parish: Parish):
        return cls(
            uuid=parish.uuid,
            name=parish.name,
            messesinfo_id=parish.messesinfo_community_id,
            website_uuid=parish.website.uuid if parish.website else None,
            created_at=parish.created_at,
            updated_at=parish.updated_at,
        )


@api.get("/parishes", response=list[ParishOut])
def api_public_parishes(request, limit: int = 10, offset: int = 0, updated_from: datetime = None
                        ) -> list[ParishOut]:
    limit = max(0, min(100, limit))
    offset = max(0, offset)

    parish_query = Parish.objects
    if updated_from:
        parish_query = parish_query.filter(updated_at__gte=updated_from)
    parishes = parish_query.order_by('updated_at').all()[offset:offset + limit]

    return list(map(ParishOut.from_parish, parishes))


############
# WEBSITES #
############

class WebsiteOut(Schema):
    uuid: UUID
    name: str
    home_url: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_website(cls, website: Website):
        return cls(
            uuid=website.uuid,
            name=website.name,
            home_url=website.home_url,
            created_at=website.created_at,
            updated_at=website.updated_at,
        )


@api.get("/websites", response=list[WebsiteOut])
def api_public_websites(request, limit: int = 10, offset: int = 0, updated_from: datetime = None
                        ) -> list[WebsiteOut]:
    limit = max(0, min(100, limit))
    offset = max(0, offset)

    website_query = Website.objects
    if updated_from:
        website_query = website_query.filter(updated_at__gte=updated_from)
    websites = website_query.order_by('updated_at').all()[offset:offset + limit]

    return list(map(WebsiteOut.from_website, websites))
