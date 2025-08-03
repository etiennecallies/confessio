import asyncio
from typing import Optional
from uuid import UUID

from django.contrib.auth.models import User
from django.db.models.functions import Now
from pydantic import BaseModel

from home.models import Pruning, Sentence
from scraping.extract.extract_content import split_and_tag, BaseActionInterface
from scraping.extract.tag_line import Tag
from scraping.extract_v2.models import TagV2, EventMotion
from scraping.extract_v2.prune_lines_v2 import get_pruned_lines_indices_v2
from scraping.extract_v2.qualify_line_interfaces import BaseQualifyLineInterface
from scraping.extract_v2.split_content import split_and_tag_v2
from scraping.prune.models import Action, Source
from scraping.prune.prune_lines import get_pruned_lines_indices
from scraping.refine.refine_content import replace_link_by_their_content
from scraping.services.prune_scraping_service import update_parsings, add_necessary_moderation_v2
from scraping.utils.html_utils import split_lines


#################
# HUMAN INDICES #
#################

class PruningHumanPiece(BaseModel):
    id: str
    do_show: bool
    text_without_link: str


def get_pruning_human_pieces(pruning: Pruning) -> list[PruningHumanPiece]:
    indices = pruning.human_indices if pruning.human_indices is not None \
        else pruning.ml_indices

    pruning_human_pieces = []
    for i, line in enumerate(split_lines(pruning.extracted_html)):
        text_without_link = replace_link_by_their_content(line)
        pruning_human_pieces.append(PruningHumanPiece(
            id=f'{i}',
            do_show=i in indices,
            text_without_link=text_without_link
        ))

    return pruning_human_pieces


def set_human_indices(pruning: Pruning, indices: list[int]):
    pruning.human_indices = indices
    pruning.pruned_indices = indices
    pruning.save()
    if pruning.ml_indices != indices:
        reset_pages_counter_of_pruning(pruning)
        asyncio.run(update_parsings(pruning))


#################
# ML INDICES V1 #
#################

class ColoredTag(BaseModel):
    name: str
    color: str


class ColoredPiece(BaseModel):
    id: str
    do_show: bool
    text: str
    color: str
    action: Action
    tags: list[ColoredTag]
    source_icon: Optional[str]
    sentence_uuid: UUID | None


def get_colored_pieces(extracted_html: str, action_interface: BaseActionInterface
                       ) -> list[ColoredPiece]:
    lines_and_tags = split_and_tag(extracted_html, action_interface)
    kept_indices = sum(get_pruned_lines_indices(lines_and_tags), [])

    tag_colors = {
        Tag.PERIOD: 'warning',
        Tag.DATE: 'primary',
        Tag.SCHEDULE: 'info',
        Tag.CONFESSION: 'success',
    }

    source_icons = {
        Source.HUMAN: 'fas fa-user',
        Source.ML: 'fas fa-robot',
    }

    colored_pieces = []
    for i, lines_and_tag in enumerate(lines_and_tags):
        new_tags = []
        for tag in lines_and_tag.tags:
            new_tags.append(ColoredTag(
                name=tag.value,
                color=tag_colors[tag]
            ))

        do_show = i in kept_indices

        colored_pieces.append(ColoredPiece(
            id=f'{i}',
            do_show=do_show,
            text=lines_and_tag.line,
            color='' if do_show else 'text-warning',
            action=lines_and_tag.action,
            tags=new_tags,
            source_icon=source_icons[lines_and_tag.source] if lines_and_tag.source else None,
            sentence_uuid=lines_and_tag.sentence_uuid,
        ))

    return colored_pieces


def update_sentence_action(sentence: Sentence, pruning: Pruning, user: User, action: Action):
    sentence.action = action
    sentence.updated_by = user
    sentence.updated_on_pruning = pruning
    sentence.source = Source.HUMAN

    sentence.save()


def set_ml_indices_as_human(pruning: Pruning):
    pruning.human_indices = pruning.ml_indices
    pruning.pruned_indices = pruning.ml_indices
    pruning.save()


#################
# ML INDICES V2 #
#################

class ColoredTagV2(BaseModel):
    name: str
    short_name: str
    color: str
    checked: bool


class ColoredPieceV2(BaseModel):
    id: str
    do_show: bool
    text: str
    color: str
    event_motion: EventMotion
    tags: list[ColoredTagV2]
    sentence_uuid: UUID | None


def get_colored_pieces_v2(extracted_html: str, qualify_line_interface: BaseQualifyLineInterface
                          ) -> list[ColoredPiece]:
    lines_and_tags = split_and_tag_v2(extracted_html, qualify_line_interface)
    kept_indices = sum(get_pruned_lines_indices_v2(lines_and_tags), [])

    tag_colors = {
        TagV2.SPECIFIER: 'purple',
        TagV2.SCHEDULE: 'tertiary',
    }
    tag_short_names = {
        TagV2.SPECIFIER: 'spec',
        TagV2.SCHEDULE: 'sched',
    }

    colored_pieces = []
    for i, line_and_tag in enumerate(lines_and_tags):
        tags = []
        for tag in TagV2:
            tags.append(ColoredTagV2(
                name=tag.value,
                short_name=tag_short_names[tag],
                color=tag_colors[tag],
                checked=tag in line_and_tag.tags,
            ))

        do_show = i in kept_indices

        colored_pieces.append(ColoredPieceV2(
            id=f'{i}',
            do_show=do_show,
            text=line_and_tag.line,
            color='' if do_show else 'text-warning',
            event_motion=line_and_tag.event_motion,
            tags=tags,
            sentence_uuid=line_and_tag.sentence_uuid,
        ))

    return colored_pieces


def set_v2_indices_as_human(pruning: Pruning):
    pruning.human_indices = pruning.v2_indices
    needs_reparse = False
    if pruning.pruned_indices != pruning.v2_indices:
        pruning.pruned_indices = pruning.v2_indices
        needs_reparse = True
    pruning.save()

    add_necessary_moderation_v2(pruning)

    if needs_reparse:
        asyncio.run(update_parsings(pruning))


######################
# VALIDATION COUNTER #
######################

def on_pruning_human_validation(pruning: Pruning):
    set_ml_indices_as_human(pruning)
    increment_counters_of_pruning(pruning)


def reset_pages_counter_of_pruning(pruning: Pruning):
    websites_to_reset = set()
    for scraping in pruning.scrapings.all():
        page = scraping.page
        page.pruning_validation_counter = -1
        page.save()
        websites_to_reset.add(page.website)

    for website in websites_to_reset:
        website.pruning_validation_counter = -1
        website.save()


def increment_counters_of_pruning(pruning: Pruning):
    websites_to_increment = set()
    for scraping in pruning.scrapings.all():
        page = scraping.page
        page.pruning_validation_counter += 1
        page.pruning_last_validated_at = Now()
        page.save()
        websites_to_increment.add(page.website)

    for website in websites_to_increment:
        website.pruning_validation_counter += 1
        website.pruning_last_validated_at = Now()
        website.save()
