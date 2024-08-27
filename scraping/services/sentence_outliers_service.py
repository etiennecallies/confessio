from home.models import Sentence, SentenceModeration, Pruning
from scraping.extract.extract_content import get_lines_without_link


##############
# MODERATION #
##############

def add_sentence_moderation(sentence: Sentence, other_action: Sentence.Action):
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


def get_pruning_containing_sentence(sentence: Sentence) -> list[Pruning]:
    all_prunings = Pruning.objects.filter(extracted_html__contains=sentence.line).all()

    prunings = []
    for pruning in all_prunings:
        print(sentence.line)
        print(get_lines_without_link(pruning.extracted_html))
        if sentence.line in get_lines_without_link(pruning.extracted_html):
            prunings.append(pruning)

    return prunings
