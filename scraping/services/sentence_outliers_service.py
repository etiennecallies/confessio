from home.models import Sentence, SentenceModeration, Pruning
from scraping.prune.models import Action
from scraping.refine.refine_content import remove_link_from_html


##############
# MODERATION #
##############

def add_sentence_moderation(sentence: Sentence, other_action: Action):
    category = SentenceModeration.Category.ML_MISMATCH

    # check if moderation already exists
    if SentenceModeration.objects.filter(sentence=sentence, category=category).exists():
        return

    sentence_moderation = SentenceModeration(
        sentence=sentence,
        category=category,
        action=sentence.action,
        other_action=other_action,
    )
    sentence_moderation.save()


def remove_sentence_not_validated_moderation(sentence: Sentence):
    category = SentenceModeration.Category.ML_MISMATCH
    SentenceModeration.objects.filter(sentence=sentence, validated_at=None, category=category
                                      ).delete()


def get_lines_without_link(refined_content: str) -> list[str]:
    results = []
    for line in refined_content.split('<br>\n'):
        results.append(remove_link_from_html(line))

    return results


def get_pruning_containing_sentence(sentence: Sentence) -> list[Pruning]:
    """Could be faster with a many-to-many relationship Sentence <-> Pruning"""

    all_prunings = Pruning.objects.filter(extracted_html__contains=sentence.line).all()

    prunings = []
    for pruning in all_prunings:
        if sentence.line in get_lines_without_link(pruning.extracted_html):
            prunings.append(pruning)

    return prunings
