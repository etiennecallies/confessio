from home.models import Sentence, SentenceModeration, Classifier
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

def get_category(target: Classifier.Target) -> SentenceModeration.Category:
    if target == Classifier.Target.SPECIFIER:
        return SentenceModeration.Category.SPECIFIER_MISMATCH
    elif target == Classifier.Target.SCHEDULE:
        return SentenceModeration.Category.SCHEDULES_MISMATCH
    elif target == Classifier.Target.CONFESSION:
        return SentenceModeration.Category.CONFESSION_MISMATCH
    else:
        raise NotImplementedError(f'Target {target} is not supported for sentence moderation')


def add_sentence_v2_moderation(sentence: Sentence, target: Classifier.Target):
    category = get_category(target)

    # check if moderation already exists
    if SentenceModeration.objects.filter(sentence=sentence, category=category).exists():
        return

    sentence_moderation = SentenceModeration(
        sentence=sentence,
        category=category,
    )
    sentence_moderation.save()


def remove_sentence_not_validated_v2_moderation(sentence: Sentence, target: Classifier.Target):
    category = get_category(target)
    SentenceModeration.objects.filter(sentence=sentence, validated_at=None, category=category
                                      ).delete()
