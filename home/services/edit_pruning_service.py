from typing import Optional
from uuid import UUID

from django.contrib.auth.models import User
from django.db.models.functions import Now
from pydantic import BaseModel

from home.models import Sentence, Pruning
from scraping.extract.extract_content import split_and_tag, BaseActionInterface
from scraping.extract.tag_line import Tag
from scraping.prune.models import Action, Source
from scraping.prune.prune_lines import get_pruned_lines_indices


############################
# ADD ID AND COLOR TO TAGS #
############################

class ColoredTag(BaseModel):
    name: str
    color: str


class ColoredPiece(BaseModel):
    id: str
    do_show: bool
    text: str
    text_without_link: str
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
            text_without_link=lines_and_tag.line_without_link,
            color='' if do_show else 'text-warning',
            action=lines_and_tag.action,
            tags=new_tags,
            source_icon=source_icons[lines_and_tag.source] if lines_and_tag.source else None,
            sentence_uuid=lines_and_tag.sentence_uuid,
        ))

    return colored_pieces


###################
# UPDATE SENTENCE #
###################

def update_sentence_action(sentence: Sentence, pruning: Pruning, user: User, action: Action):
    sentence.action = action
    sentence.updated_by = user
    sentence.updated_on_pruning = pruning
    sentence.source = Source.HUMAN

    sentence.save()


######################
# VALIDATION COUNTER #
######################

def reset_pages_counter_of_pruning(pruning: Pruning):
    websites_to_reset = set()
    for scraping in pruning.scrapings.all():
        page = scraping.temp_page
        page.pruning_validation_counter = -1
        page.save()
        websites_to_reset.add(page.website)

    for website in websites_to_reset:
        website.pruning_validation_counter = -1
        website.save()


def increment_page_validation_counter_of_pruning(pruning: Pruning):
    websites_to_increment = set()
    for scraping in pruning.scrapings.all():
        page = scraping.temp_page
        page.pruning_validation_counter += 1
        page.pruning_last_validated_at = Now()
        page.save()
        websites_to_increment.add(page.website)

    for website in websites_to_increment:
        website.pruning_validation_counter += 1
        website.pruning_last_validated_at = Now()
        website.save()
