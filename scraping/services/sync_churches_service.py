from abc import ABC, abstractmethod
from typing import Optional

from home.models import Parish, Diocese, Church, ExternalSource, \
    ChurchModeration
from scraping.services.chuch_location_service import compute_church_coordinates
from scraping.services.church_name_service import sort_by_name_similarity
from scraping.utils.geo_utils import get_geo_distance


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
    def is_same_parish(self, parish1: Parish, parish2: Parish) -> bool:
        pass

    @abstractmethod
    def get_churches_of_same_parish(self, external_church: Church) -> set[Church]:
        pass

    @abstractmethod
    def retrieve_parish(self, external_parish: Parish) -> Parish:
        pass

    @abstractmethod
    def is_same_church_set(self, church_set1: Optional[set[Church]],
                           church_set2: Optional[set[Church]]) -> bool:
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

    def is_same_parish(self, parish1: Optional[Parish], parish2: Optional[Parish]) -> bool:
        if parish1 is None and parish2 is None:
            return True

        if parish1 is None or parish2 is None:
            return False

        return parish1.messesinfo_community_id == parish2.messesinfo_community_id

    def get_churches_of_same_parish(self, external_church: Church) -> set[Church]:
        return set(Church.objects.filter(
            parish__messesinfo_community_id=external_church.parish.messesinfo_community_id).all())

    def retrieve_parish(self, external_parish: Parish) -> Parish:
        return Parish.objects.get(messesinfo_community_id=external_parish.messesinfo_community_id)

    def is_same_church_set(self, church_set1: Optional[set[Church]],
                           church_set2: Optional[set[Church]]) -> bool:
        return set([c.messesinfo_id for c in (church_set1 or set())]) \
            == set([c.messesinfo_id for c in (church_set2 or set())])


###############
# CHURCH SYNC #
###############

def add_church_moderation_if_not_exists(church_moderation: ChurchModeration,
                                        church_retriever: ChurchRetriever,
                                        similar_churches: Optional[set[Church]] = None):
    try:
        existing_moderation = ChurchModeration.objects.get(
            church=church_moderation.church,
            category=church_moderation.category,
            source=church_moderation.source
        )
        if existing_moderation.name != church_moderation.name \
                or not church_retriever.is_same_parish(existing_moderation.parish,
                                                       church_moderation.parish) \
                or not church_retriever.is_same_church_set(
                    set(existing_moderation.similar_churches.all()), similar_churches):
            existing_moderation.delete()
            church_moderation.save()
            if similar_churches:
                church_moderation.similar_churches.set(similar_churches)
    except ChurchModeration.DoesNotExist:
        church_moderation.save()
        if similar_churches:
            church_moderation.similar_churches.set(similar_churches)


def update_church(church: Church, external_church: Church, church_retriever: ChurchRetriever):
    # Check name
    if church.name != external_church.name:
        add_church_moderation_if_not_exists(ChurchModeration(
            church=church, category=ChurchModeration.Category.NAME_DIFFERS,
            source=church_retriever.source, name=external_church.name), church_retriever)

    # Check parish
    if not church_retriever.is_same_parish(church.parish, external_church.parish):
        external_parish = save_parish(external_church.parish, church_retriever)
        add_church_moderation_if_not_exists(ChurchModeration(
            church=church, category=ChurchModeration.Category.PARISH_DIFFERS,
            source=church_retriever.source, parish=external_parish), church_retriever)

    # Location
    if church.location != external_church.location or church.address != external_church.address \
            or church.zipcode != external_church.zipcode or church.city != external_church.city:
        add_church_moderation_if_not_exists(ChurchModeration(
            church=church, category=ChurchModeration.Category.LOCATION_DIFFERS,
            source=church_retriever.source, location=external_church.location,
            address=external_church.address, zipcode=external_church.zipcode,
            city=external_church.city), church_retriever)


def look_for_similar_churches_by_name(external_church: Church,
                                      diocese_churches: list[Church]) -> set[Church]:
    sorted_churches = sort_by_name_similarity(external_church, diocese_churches)

    return set(sorted_churches[:3])


def look_for_similar_churches_by_distance(external_church, diocese_churches) -> set[Church]:
    if external_church.location is None:
        return set()

    distance_tuples = []
    for church in diocese_churches:
        if church.location is None:
            continue

        distance_tuples.append((get_geo_distance(external_church.location, church.location),
                                church))

    # keep only the three closest churches
    closest_churches = sorted(distance_tuples, key=lambda t: t[0], reverse=False)[:3]
    if not closest_churches:
        return set()

    _, similar_churches = zip(*closest_churches)

    return set(similar_churches)


def look_for_similar_churches(external_church: Church, diocese_churches: list[Church],
                              church_retriever: ChurchRetriever) -> set[Church]:
    similar_churches = set()

    # 1. Check if there is a church with the same parish
    assert external_church.parish
    similar_churches |= church_retriever.get_churches_of_same_parish(external_church)

    # 2. Check if there is a parish with the same name
    similar_churches |= look_for_similar_churches_by_name(external_church, diocese_churches)

    # 3. Check for the closest churches
    similar_churches |= look_for_similar_churches_by_distance(external_church, diocese_churches)

    return similar_churches


def sync_churches(external_churches: list[Church],
                  diocese: Diocese,
                  church_retriever: ChurchRetriever,
                  allow_no_url: bool = False):
    # get all churches in the diocese
    diocese_churches = Church.objects.filter(parish__diocese=diocese).all()

    print('looping through external churches')
    for external_church in external_churches:
        confessio_church = church_retriever.retrieve_church(external_church)
        if confessio_church:
            # Church already exists, we update it
            update_church(confessio_church, external_church, church_retriever)
        else:
            if not allow_no_url and not external_church.parish.website:
                # We don't really care if there is a new church whose parish does not have a website
                continue

            if external_church.location is not None:
                church_with_same_location = get_church_with_same_location(external_church)
                if church_with_same_location:
                    add_church_moderation_if_not_exists(ChurchModeration(
                        church=church_with_same_location,
                        category=ChurchModeration.Category.LOCATION_CONFLICT,
                        source=church_retriever.source,
                        name=external_church.name,
                        address=external_church.address,
                        zipcode=external_church.zipcode,
                        city=external_church.city,
                        messesinfo_id=external_church.messesinfo_id,
                    ), church_retriever)
                    continue

            # Church does not exist, finding similar churches or create it
            similar_churches = look_for_similar_churches(external_church, diocese_churches,
                                                         church_retriever)

            save_church(external_church, church_retriever)

            add_church_moderation_if_not_exists(ChurchModeration(
                church=external_church,
                category=ChurchModeration.Category.ADDED_CHURCH,
                source=church_retriever.source,
            ), church_retriever, similar_churches=similar_churches)

    print('looping through diocese churches')
    for church in diocese_churches:
        if not church_retriever.church_exists_in_list(church, external_churches):
            add_church_moderation_if_not_exists(ChurchModeration(
                church=church,
                category=ChurchModeration.Category.DELETED_CHURCH,
                source=church_retriever.source,
            ), church_retriever)


###############
# CHURCH SAVE #
###############

def save_parish(parish: Parish, church_retriever: ChurchRetriever) -> Parish:
    try:
        return church_retriever.retrieve_parish(parish)
    except Parish.DoesNotExist:
        parish.save()
        return parish


def save_church(church: Church, church_retriever: ChurchRetriever):
    if church_retriever.retrieve_church(church):
        return

    church.parish = save_parish(church.parish, church_retriever)
    church.save()
    if not church.location.x or not church.location.y:
        compute_church_coordinates(church, church_retriever.source)


def get_church_with_same_location(church: Church) -> Optional[Church]:
    try:
        return Church.objects.get(location=church.location)
    except Church.DoesNotExist:
        return None
