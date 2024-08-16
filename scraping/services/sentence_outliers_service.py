from home.models import Sentence, SentenceModeration


def add_sentence_moderation(sentence: Sentence):
    category = SentenceModeration.Category.ML_MISMATCH

    # check if moderation already exists
    if SentenceModeration.objects.filter(sentence=sentence, category=category).exists():
        return

    sentence_moderation = SentenceModeration(
        sentence=sentence,
        category=category,
        action=sentence.action,
    )
    sentence_moderation.save()

def remove_sentence_not_validated_moderation(sentence: Sentence):
    category = SentenceModeration.Category.ML_MISMATCH
    SentenceModeration.objects.filter(sentence=sentence, validated_at=None, category=category).delete()
