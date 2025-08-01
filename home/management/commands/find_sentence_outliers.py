from home.management.abstract_command import AbstractCommand
from home.models import Classifier
from scraping.services.classify_sentence_service import classify_existing_sentence
from scraping.services.sentence_outliers_service import add_sentence_moderation, \
    remove_sentence_not_validated_moderation
from scraping.services.train_classifier_service import build_sentence_dataset, extract_label


class Command(AbstractCommand):
    help = ("Launch the inference of latest classifier and find mismatch between prediction and "
            "human label")

    def handle(self, *args, **options):
        target = Classifier.Target.ACTION
        self.info(f'Building sentence dataset for target {target}...')

        sentence_dataset = build_sentence_dataset(target)
        if not sentence_dataset:
            self.warning(f'No sentence found')
            return

        self.info(f'Got {len(sentence_dataset)} sentences for target {target}')

        nb_sentence_outliers = 0
        for sentence in sentence_dataset:
            human_label = extract_label(sentence, target)
            label, _ = classify_existing_sentence(sentence, target)
            if label != human_label:
                self.warning(f'Got {label} vs human label {human_label} '
                             f'on line "{sentence.line}"')
                nb_sentence_outliers += 1
                add_sentence_moderation(sentence, other_action=label)
            else:
                remove_sentence_not_validated_moderation(sentence)

        self.success(f'Done! Got {nb_sentence_outliers} sentence outliers '
                     f'({nb_sentence_outliers / len(sentence_dataset) * 100:.2f} %)')
