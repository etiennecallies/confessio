from datetime import datetime
from uuid import UUID

from django.db.models import Exists, OuterRef
from ninja import NinjaAPI, Schema, Field

from home.models import Church, ChurchModeration

api = NinjaAPI()


class ChurchOut(Schema):
    name: str
    latitude: float
    longitude: float
    address: str | None
    zipcode: str | None
    city: str | None
    messesinfo_id: str | None
    wikidata_id: str | None
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
            name=church.name,
            latitude=church.location.y,
            longitude=church.location.x,
            address=church.address,
            zipcode=church.zipcode,
            city=church.city,
            messesinfo_id=church.messesinfo_id,
            wikidata_id=church.wikidata_id,
            parish_uuid=church.parish_id,
            is_active=church.is_active,
            created_at=church.created_at,
            updated_at=church.updated_at,
            has_validated_moderation=church.has_validated_moderation,
            has_unvalidated_moderation=church.has_unvalidated_moderation,
        )


@api.get("/churches", response=list[ChurchOut])
def add(request, limit: int = 10, offset: int = 0, updated_from: datetime = None
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
