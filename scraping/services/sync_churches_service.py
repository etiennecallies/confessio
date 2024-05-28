from abc import ABC, abstractmethod
from typing import Optional

from home.models import Parish, Diocese, Church, ExternalSource, \
    ChurchModeration
from home.services.autocomplete_service import get_string_distance
from scraping.services.chuch_location_service import compute_church_coordinates


####################
# CHURCH RETRIEVAL #
####################

class ChurchRetriever(ABC):
    @property
    @abstractmethod
    def source(self) -> ExternalSource:
        pass

    @abstractmethod
    def retrieve_church(self, external_church: Church) -> Optional[Church]:
        pass

    @abstractmethod
    def church_exists_in_list(self, church: Church,
                              external_churches: list[Church]) -> bool:
        pass

    @abstractmethod
    def has_same_parish(self, church: Church, external_church: Church) -> bool:
        pass

    @abstractmethod
    def get_churches_of_same_parish(self, external_church: Church) -> set[Church]:
        pass


class MessesinfoChurchRetriever(ChurchRetriever):
    source = ExternalSource.MESSESINFO

    def retrieve_church(self, external_church: Church) -> Optional[Church]:
        try:
            return Church.objects.get(messesinfo_id=external_church.messesinfo_id)
        except Church.DoesNotExist:
            return None

    def church_exists_in_list(self, church: Church, external_churches: list[Church]) -> bool:
        for external_church in external_churches:
            if external_church.messesinfo_id == church.messesinfo_id:
                return True
        return False

    def has_same_parish(self, church: Church, external_church: Church) -> bool:
        return church.parish.messesinfo_community_id == \
            external_church.parish.messesinfo_community_id

    def get_churches_of_same_parish(self, external_church: Church) -> set[Church]:
        return set(Church.objects.filter(
            parish__messesinfo_community_id=external_church.parish.messesinfo_community_id).all())


###############
# CHURCH SYNC #
###############

def add_church_moderation_if_not_exists(church_moderation: ChurchModeration):
    try:
        existing_moderation = ChurchModeration.objects.get(
            church=church_moderation.church,
            category=church_moderation.category,
            source=church_moderation.source
        )
        if existing_moderation.name != church_moderation.name \
                or existing_moderation.parish != church_moderation.parish:
            existing_moderation.delete()
            church_moderation.save()
    except ChurchModeration.DoesNotExist:
        church_moderation.save()


def update_church(church: Church, external_church: Church, church_retriever: ChurchRetriever):
    # Check name
    if church.name != external_church.name:
        add_church_moderation_if_not_exists(ChurchModeration(
            church=church, category=ChurchModeration.Category.NAME_DIFFERS,
            source=church_retriever.source, name=external_church.name))

    # Check parish
    if not church_retriever.has_same_parish(church, external_church):
        add_church_moderation_if_not_exists(ChurchModeration(
            church=church, category=ChurchModeration.Category.PARISH_DIFFERS,
            source=church_retriever.source, parish=external_church.parish))

    # Location
    if church.location != external_church.location or church.address != external_church.address \
            or church.zipcode != external_church.zipcode or church.city != external_church.city:
        add_church_moderation_if_not_exists(ChurchModeration(
            church=church, category=ChurchModeration.Category.LOCATION_DIFFERS,
            source=church_retriever.source, location=external_church.location,
            address=external_church.address, zipcode=external_church.zipcode,
            city=external_church.city))


def look_for_similar_churches_by_name(external_church: Church,
                                      diocese_churches: list[Church]) -> set[Church]:
    tuples = zip(map(lambda p: get_string_distance(external_church.name, p.name), diocese_churches),
                 diocese_churches)
    # keep only the three closest churches
    closest_churches = sorted(tuples, key=lambda t: t[0])[:3]
    _, similar_churches = zip(*closest_churches)

    return set(similar_churches)


def look_for_similar_churches(external_church: Church, diocese_churches: list[Church],
                              church_retriever: ChurchRetriever) -> set[Parish]:
    similar_churches = set()

    # 1. Check if there is a church with the same parish
    assert external_church.parish
    similar_churches |= church_retriever.get_churches_of_same_parish(external_church)

    # 2. Check if there is a parish with the same name
    similar_churches |= look_for_similar_churches_by_name(external_church, diocese_churches)

    # TODO look for the closest church in the diocese by geographical distance

    return similar_churches


def sync_churches(external_churches: list[Church],
                  diocese: Diocese,
                  church_retriever: ChurchRetriever):
    # get all churches in the diocese
    diocese_churches = Church.objects.filter(parish__diocese=diocese).all()

    print('looping through external churches')
    for external_church in external_churches:
        confessio_church = church_retriever.retrieve_church(external_church)
        if confessio_church:
            # Church already exists, we update it
            update_church(confessio_church, external_church, church_retriever)
        else:
            if not external_church.parish.website:
                # We don't really care if there is a new church whose parish does not have a website
                continue

            # Church does not exist, finding similar churches or create it
            similar_churches = look_for_similar_churches(external_church, diocese_churches,
                                                         church_retriever)

            save_church(external_church, church_retriever)

            add_church_moderation_if_not_exists(ChurchModeration(
                church=external_church,
                category=ChurchModeration.Category.ADDED_CHURCH,
                source=church_retriever.source,
                similar_churches=similar_churches,
            ))

    print('looping through diocese churches')
    for church in diocese_churches:
        if not church_retriever.church_exists_in_list(church, external_churches):
            add_church_moderation_if_not_exists(ChurchModeration(
                church=church,
                category=ChurchModeration.Category.DELETED_CHURCH,
                source=church_retriever.source,
            ))



###############
# CHURCH SAVE #
###############

def save_church(church: Church, church_retriever: ChurchRetriever):
    church.save()
    if not church.location.x or not church.location.y:
        compute_church_coordinates(church, church_retriever.source)
