from typing import Optional

from django.contrib.auth.models import User

from home.models import Sentence, Scraping
from scraping.extract.extract_content import split_and_tag, BaseTagInterface
from scraping.extract.tag_line import Tag
from scraping.prune.models import Action
from scraping.prune.prune_lines import get_pruned_lines_indices
from scraping.prune.transform_sentence import get_transformer
from scraping.services.classify_sentence_service import action_to_db_action


############################
# ADD ID AND COLOR TO TAGS #
############################

def get_colored_pieces(confession_html: str, tag_interface: BaseTagInterface):
    lines_and_tags = split_and_tag(confession_html, tag_interface)
    kept_indices = get_pruned_lines_indices(lines_and_tags)

    tag_colors = {
        Tag.PERIOD: 'warning',
        Tag.DATE: 'primary',
        Tag.SCHEDULE: 'info',
        Tag.CONFESSION: 'success',
    }

    colored_pieces = []
    for i, (text, text_without_link, tags, action) in enumerate(lines_and_tags):
        new_tags = []
        for tag in tags:
            new_tags.append({
                'name': tag.value,
                'color': tag_colors[tag]
            })

        do_show = i in kept_indices
        colored_pieces.append(
            {
                "id": f'{i}',
                "do_show": do_show,
                "text": text,
                "text_without_link": text_without_link,
                "color": '' if do_show else 'text-warning',
                "action": action,
                "tags": new_tags
            }
        )

    return colored_pieces


#################
# SAVE SENTENCE #
#################

def save_sentence(line_without_link: str, scraping: Optional[Scraping], user: User, action: Action):
    db_action = action_to_db_action(action)

    try:
        sentence = Sentence.objects.get(line=line_without_link)
        if sentence.action == db_action and sentence.source == Sentence.Source.HUMAN:
            # We do nothing if action is the same
            return

        sentence.action = db_action
        sentence.updated_by = user
        sentence.scraping = scraping
        sentence.source = Sentence.Source.HUMAN

        # TODO remove this
        transformer = get_transformer()
        embedding = transformer.transform(line_without_link)
        sentence.embedding = embedding
        sentence.transformer_name = transformer.get_name()
    except Sentence.DoesNotExist:
        # TODO this should never happen eventually

        transformer = get_transformer()
        embedding = transformer.transform(line_without_link)

        sentence = Sentence(
            line=line_without_link,
            scraping=scraping,
            updated_by=user,
            action=db_action,
            source=Sentence.Source.HUMAN,
            transformer_name=transformer.get_name(),
            embedding=embedding,
        )

    sentence.save()
