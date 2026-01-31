from registry.models import Sentence, SentenceModeration
from scraping.prune.models import Action


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


#################
# V2 MODERATION #
#################

def add_sentence_v2_moderation(sentence: Sentence):
    category = SentenceModeration.Category.CONFESSION_OUTLIER

    # check if moderation already exists
    if SentenceModeration.objects.filter(sentence=sentence, category=category).exists():
        return

    sentence_moderation = SentenceModeration(
        sentence=sentence,
        category=category,
    )
    sentence_moderation.save()


def remove_sentence_not_validated_v2_moderation(sentence: Sentence):
    category = SentenceModeration.Category.CONFESSION_OUTLIER
    SentenceModeration.objects.filter(sentence=sentence, category=category).delete()
