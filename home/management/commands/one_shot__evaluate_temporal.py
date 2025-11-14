from home.management.abstract_command import AbstractCommand
from home.models import Classifier
from scraping.extract_v2.models import Temporal
from scraping.services.classify_sentence_service import get_ml_label
from scraping.services.train_classifier_service import build_sentence_dataset, extract_label
from scraping.utils.enum_utils import BooleanStringEnum


class Command(AbstractCommand):
    help = ("One shot command to evaluate temporal classifier")

    def handle(self, *args, **options):
        target = Classifier.Target.TEMPORAL
        self.info(f'Finding sentence outliers for target {target}...')
        sentence_dataset = build_sentence_dataset(target)
        if not sentence_dataset:
            self.warning(f'No sentence found')
            return

        self.info(f'Got {len(sentence_dataset)} sentences for target {target}')

        total = 0
        temporal_success = 0
        mixed_success = 0
        for sentence in sentence_dataset:
            total += 1

            human_temporal = extract_label(sentence, Classifier.Target.TEMPORAL)
            ml_temporal = get_ml_label(sentence, Classifier.Target.TEMPORAL)

            if ml_temporal == human_temporal:
                temporal_success += 1

            ml_schedule = get_ml_label(sentence, Classifier.Target.SCHEDULE)
            ml_specifier = get_ml_label(sentence, Classifier.Target.SPECIFIER)
            if ml_schedule == BooleanStringEnum.TRUE and ml_specifier == BooleanStringEnum.TRUE:
                continue

            mixed_temporal = Temporal.SPEC if ml_specifier == BooleanStringEnum.TRUE else (
                Temporal.SCHED if ml_schedule == BooleanStringEnum.TRUE
                else Temporal.NONE
            )

            if mixed_temporal == human_temporal:
                mixed_success += 1

        self.success(f'TEMPORAL accuracy: {temporal_success} / {total} '
                     f'({temporal_success / total * 100:.2f} %)')
        self.success(f'MIXED accuracy: {mixed_success} / {total} '
                     f'({mixed_success / total * 100:.2f} %)')
