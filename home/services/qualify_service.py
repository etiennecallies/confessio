from django.contrib.auth.models import User

from home.models import Sentence, Scraping
from scraping.prune.models import Action
from scraping.services.prune_scraping_service import SentenceFromDbTagInterface
from scraping.extract.extract_content import split_and_tag
from scraping.prune.prune_lines import get_pruned_lines_indices
from scraping.extract.tag_line import Tag


############################
# ADD ID AND COLOR TO TAGS #
############################

def get_colored_pieces(confession_html: str):
    lines_and_tags = split_and_tag(confession_html, SentenceFromDbTagInterface())
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

        colored_pieces.append(
            {
                "id": f'{i}',
                "text": text,
                "text_without_link": text_without_link,
                "color": '' if i in kept_indices else 'text-warning',
                "action": action,
                "tags": new_tags
            }
        )

    return colored_pieces


#################
# SAVE SENTENCE #
#################

def save_sentence(line_without_link: str, scraping: Scraping, user: User, action: Action):
    db_action = {
        Action.SHOW: Sentence.Action.SHOW,
        Action.HIDE: Sentence.Action.HIDE,
        Action.STOP: Sentence.Action.STOP,
    }[action]

    try:
        sentence = Sentence.objects.get(line=line_without_link)
        if sentence.action == db_action:
            # We do nothing if action is the same
            return

        sentence.action = db_action
    except Sentence.DoesNotExist:
        if db_action == Sentence.Action.SHOW:
            # We don't save sentence if it is default value
            return

        sentence = Sentence(
            line=line_without_link,
            scraping=scraping,
            updated_by=user,
            action=db_action,
        )

    sentence.save()
