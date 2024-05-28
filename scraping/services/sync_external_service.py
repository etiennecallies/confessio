from abc import ABC, abstractmethod
from typing import Optional

from home.models import Parish, Diocese, Church, ParishModeration, Website, ExternalSource, \
    ChurchModeration
from home.services.autocomplete_service import get_string_distance


####################
# PARISH RETRIEVAL #
####################

class ParishRetriever(ABC):
    @property
    @abstractmethod
    def source(self) -> ExternalSource:
        pass

    @abstractmethod
    def retrieve_parish(self, external_parish: Parish) -> Optional[Parish]:
        pass


class MessesinfoParishRetriever(ParishRetriever):
    source = ExternalSource.MESSESINFO

    def retrieve_parish(self, external_parish: Parish) -> Optional[Parish]:
        try:
            return Parish.objects.get(
                messesinfo_community_id=external_parish.messesinfo_community_id)
        except Parish.DoesNotExist:
            return None


###############
# PARISH SYNC #
###############

def add_parish_moderation_if_not_exists(parish_moderation: ParishModeration):
    try:
        existing_moderation = ParishModeration.objects.get(
            parish=parish_moderation.parish,
            category=parish_moderation.category,
            source=parish_moderation.source
        )
        if existing_moderation.name != parish_moderation.name \
                or existing_moderation.website != parish_moderation.website \
                or existing_moderation.similar_parishes != parish_moderation.similar_parishes:
            existing_moderation.delete()
            parish_moderation.save()
    except ParishModeration.DoesNotExist:
        parish_moderation.save()


def update_parish(parish: Parish,
                  external_parish: Parish,
                  parish_retriever: ParishRetriever):
    # Check name
    if parish.name != external_parish.name:
        add_parish_moderation_if_not_exists(ParishModeration(
            parish=parish, category=ParishModeration.Category.NAME_DIFFERS,
            source=parish_retriever.source, name=external_parish.name))

    # Check website
    if external_parish.website:
        if parish.website and parish.website.home_url == external_parish.website.home_url:
            return

        try:
            website = Website.objects.get(home_url=external_parish.website.home_url)
        except Website.DoesNotExist:
            website = external_parish.website
            website.save()

        if not parish.website:
            parish.website = website
            parish.save()
        else:
            add_parish_moderation_if_not_exists(ParishModeration(
                parish=parish, category=ParishModeration.Category.WEBSITE_DIFFERS,
                source=parish_retriever.source, website=website))


def look_for_similar_parishes_by_name(external_parish: Parish,
                                      diocese_parishes: list[Parish]) -> set[Parish]:
    # get the distance between the external parish and all the parishes in the diocese
    tuples = zip(map(lambda p: get_string_distance(external_parish.name, p.name), diocese_parishes),
                 diocese_parishes)
    # keep only the three closest parishes
    closest_parishes = sorted(tuples, key=lambda t: t[0])[:3]
    _, similar_parishes = zip(*closest_parishes)

    return set(similar_parishes)


def look_for_similar_parishes(external_parish: Parish, diocese: Diocese) -> set[Parish]:
    similar_parishes = set()

    # 1. Check if there is a parish with the same website
    assert external_parish.website
    similar_parishes |= set(Parish.objects.filter(
        website__home_url=external_parish.website.home_url).all())

    # get all parishes in the diocese
    diocese_parishes = diocese.parishes.all()

    # 2. Check if there is a parish with the same name
    similar_parishes |= look_for_similar_parishes_by_name(external_parish, diocese_parishes)

    # TODO look for the closest parish in the diocese by geographical distance

    return similar_parishes


def sync_parishes(external_parishes: list[Parish],
                  diocese: Diocese,
                  parish_retriever: ParishRetriever):
    for external_parish in external_parishes:
        confessio_parish = parish_retriever.retrieve_parish(external_parish)
        if confessio_parish:
            # Parish already exists, we update it
            update_parish(confessio_parish, external_parish, parish_retriever)
        else:
            # Parish does not exist, finding similar parishes or create it

            if not external_parish.website:
                # We don't really care if there is a new parish without a website
                continue

            similar_parishes = look_for_similar_parishes(external_parish, diocese)

            save_parish(external_parish)

            add_parish_moderation_if_not_exists(ParishModeration(
                parish=external_parish,
                category=ParishModeration.Category.MISSING_PARISH,
                source=parish_retriever.source,
                similar_parishes=similar_parishes,
            ))


###############
# PARISH SAVE #
###############

def save_website(website: Website):
    try:
        return Website.objects.get(home_url=website.home_url)
    except Website.DoesNotExist:
        website.save()
        return website


def save_parish(parish: Parish):
    parish.website = save_website(parish.website)
    parish.save()


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


def look_for_similar_churches(external_church: Church, diocese: Diocese,
                              church_retriever: ChurchRetriever) -> set[Parish]:
    similar_churches = set()

    # 1. Check if there is a church with the same parish
    assert external_church.parish
    similar_churches |= church_retriever.get_churches_of_same_parish(external_church)

    # get all churches in the diocese
    diocese_churches = Church.objects.filter(parish__diocese=diocese).all()

    # 2. Check if there is a parish with the same name
    similar_churches |= look_for_similar_churches_by_name(external_church, diocese_churches)

    # TODO look for the closest church in the diocese by geographical distance

    return similar_churches


def sync_churches(external_churches: list[Church],
                  diocese: Diocese,
                  church_retriever: ChurchRetriever):
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
            similar_churches = look_for_similar_churches(external_church, diocese, church_retriever)

            save_church(external_church)

            add_church_moderation_if_not_exists(ChurchModeration(
                church=external_church,
                category=ChurchModeration.Category.MISSING_CHURCH,
                source=church_retriever.source,
                similar_churches=similar_churches,
            ))


###############
# CHURCH SAVE #
###############

def save_church(church: Church):
    print(f'Would have saved church {church.name}')
    # church.save()
    # if not church.location.x or not church.location.y:
    #     compute_church_coordinates(church)
