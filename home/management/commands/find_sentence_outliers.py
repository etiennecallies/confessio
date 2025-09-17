from home.management.abstract_command import AbstractCommand
from home.models import Classifier
from scraping.prune.models import Action
from scraping.services.classify_sentence_service import get_ml_label
from scraping.services.sentence_outliers_service import add_sentence_moderation, \
    remove_sentence_not_validated_moderation, add_sentence_v2_moderation, \
    remove_sentence_not_validated_v2_moderation
from scraping.services.train_classifier_service import build_sentence_dataset, extract_label
from scraping.utils.ram_utils import print_memory_usage


class Command(AbstractCommand):
    help = ("Launch the inference of latest classifier and find mismatch between prediction and "
            "human label")

    def add_arguments(self, parser):
        parser.add_argument('-t', '--target', type=Classifier.Target,
                            choices=list(Classifier.Target), help='Target of the classifier')

    def handle(self, *args, **options):
        target = options['target']
        if target:
            targets = [target]
        else:
            targets = [Classifier.Target.ACTION, Classifier.Target.CONFESSION]

        for target in targets:
            self.handle_for_target(target)

    def handle_for_target(self, target: Classifier.Target):
        self.info(f'Finding sentence outliers for target {target}...')
        print_memory_usage()
        sentence_dataset = build_sentence_dataset(target)
        if not sentence_dataset:
            self.warning(f'No sentence found')
            return

        self.info(f'Got {len(sentence_dataset)} sentences for target {target}')
        print_memory_usage()

        nb_sentence_outliers = 0
        i = 0
        for sentence in sentence_dataset:
            if i % 100 == 0:
                print_memory_usage()
            i += 1

            if target == Classifier.Target.ACTION:
                human_label = extract_label(sentence, target)
                ml_label = get_ml_label(sentence, target)
                if ml_label != human_label:
                    self.warning(f'Got {ml_label} vs human label {human_label} '
                                 f'on line "{sentence.line}"')
                    nb_sentence_outliers += 1
                    assert isinstance(ml_label, Action)
                    add_sentence_moderation(sentence, other_action=ml_label)
                else:
                    remove_sentence_not_validated_moderation(sentence)
            else:
                human_confession = extract_label(sentence, Classifier.Target.CONFESSION)
                human_schedule = extract_label(sentence, Classifier.Target.SCHEDULE)
                human_specifier = extract_label(sentence, Classifier.Target.SPECIFIER)

                ml_confession = get_ml_label(sentence, Classifier.Target.CONFESSION)
                ml_schedule = get_ml_label(sentence, Classifier.Target.SCHEDULE)
                ml_specifier = get_ml_label(sentence, Classifier.Target.SPECIFIER)

                if human_confession != ml_confession or human_schedule != ml_schedule or \
                        human_specifier != ml_specifier:
                    nb_sentence_outliers += 1
                    if i % 100 == 0:
                        print_memory_usage('before add_sentence_v2_moderation')
                    add_sentence_v2_moderation(sentence)
                    if i % 100 == 0:
                        print_memory_usage('after add_sentence_v2_moderation')
                else:
                    if i % 100 == 0:
                        print_memory_usage('before remove_sentence_not_validated_v2_moderation')
                    remove_sentence_not_validated_v2_moderation(sentence)
                    if i % 100 == 0:
                        print_memory_usage('after remove_sentence_not_validated_v2_moderation')

        self.success(f'Done! Got {nb_sentence_outliers} sentence outliers '
                     f'({nb_sentence_outliers / len(sentence_dataset) * 100:.2f} %)')
