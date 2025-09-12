from home.management.abstract_command import AbstractCommand
from home.models import SentenceModeration, Classifier
from scraping.services.classify_sentence_service import get_ml_label
from scraping.services.train_classifier_service import extract_label


class Command(AbstractCommand):
    help = "One shot command to migrate sentence v2 moderations."

    def handle(self, *args, **options):
        counter = 0
        for sentence_moderation in SentenceModeration.objects.filter(
            category__in=(SentenceModeration.Category.SPECIFIER_MISMATCH,
                          SentenceModeration.Category.SCHEDULES_MISMATCH,
                          SentenceModeration.Category.CONFESSION_MISMATCH)
        ).all():
            sentence = sentence_moderation.sentence

            human_confession = extract_label(sentence, Classifier.Target.CONFESSION)
            human_schedule = extract_label(sentence, Classifier.Target.SCHEDULE)
            human_specifier = extract_label(sentence, Classifier.Target.SPECIFIER)

            ml_confession = get_ml_label(sentence, Classifier.Target.CONFESSION)
            ml_schedule = get_ml_label(sentence, Classifier.Target.SCHEDULE)
            ml_specifier = get_ml_label(sentence, Classifier.Target.SPECIFIER)

            if human_confession != ml_confession or human_schedule != ml_schedule or \
                    human_specifier != ml_specifier:
                if not SentenceModeration.objects.filter(
                    sentence=sentence,
                    category=SentenceModeration.Category.CONFESSION_OUTLIER
                ).exists():
                    new_sentence_moderation = SentenceModeration(
                        sentence=sentence,
                        category=SentenceModeration.Category.CONFESSION_OUTLIER,
                        validated_at=sentence_moderation.validated_at,
                        validated_by=sentence_moderation.validated_by,
                        diocese=sentence_moderation.diocese,
                        created_at=sentence_moderation.created_at,
                        updated_at=sentence_moderation.updated_at,
                    )
                    new_sentence_moderation.save()

            sentence_moderation.delete()

            counter += 1
            if counter % 100 == 0:
                self.stdout.write(f'Processed {counter} sentence_moderations...')

        self.success(f'Successfully migrate {counter} v2 sentence_moderations.')
