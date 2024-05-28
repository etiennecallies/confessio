from abc import ABC, abstractmethod
from typing import Optional

from home.models import Parish, Diocese, ParishModeration, Website, ExternalSource
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

    @abstractmethod
    def parish_exists_in_list(self, parish: Parish,
                              external_parishes: list[Parish]) -> bool:
        pass


class MessesinfoParishRetriever(ParishRetriever):
    source = ExternalSource.MESSESINFO

    def retrieve_parish(self, external_parish: Parish) -> Optional[Parish]:
        try:
            return Parish.objects.get(
                messesinfo_community_id=external_parish.messesinfo_community_id)
        except Parish.DoesNotExist:
            return None

    def parish_exists_in_list(self, parish: Parish,
                              external_parishes: list[Parish]) -> bool:
        for external_parish in external_parishes:
            if external_parish.messesinfo_community_id == parish.messesinfo_community_id:
                return True

        return False


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


def look_for_similar_parishes(external_parish: Parish,
                              diocese_parishes: list[Parish]) -> set[Parish]:
    similar_parishes = set()

    # 1. Check if there is a parish with the same website
    assert external_parish.website
    similar_parishes |= set(Parish.objects.filter(
        website__home_url=external_parish.website.home_url).all())

    # 2. Check if there is a parish with the same name
    similar_parishes |= look_for_similar_parishes_by_name(external_parish, diocese_parishes)

    # TODO look for the closest parish in the diocese by geographical distance

    return similar_parishes


def sync_parishes(external_parishes: list[Parish],
                  diocese: Diocese,
                  parish_retriever: ParishRetriever):
    # get all parishes in the diocese
    diocese_parishes = diocese.parishes.all()

    print('looping through external parishes')
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

            similar_parishes = look_for_similar_parishes(external_parish, diocese_parishes)

            save_parish(external_parish)

            add_parish_moderation_if_not_exists(ParishModeration(
                parish=external_parish,
                category=ParishModeration.Category.ADDED_PARISH,
                source=parish_retriever.source,
                similar_parishes=similar_parishes,
            ))

    print('looping on diocese parishes')
    for parish in diocese_parishes:
        if not parish_retriever.parish_exists_in_list(parish, external_parishes):
            add_parish_moderation_if_not_exists(ParishModeration(
                parish=parish,
                category=ParishModeration.Category.DELETED_PARISH,
                source=parish_retriever.source,
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
