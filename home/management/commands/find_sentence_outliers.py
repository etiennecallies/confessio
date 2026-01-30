from home.management.abstract_command import AbstractCommand
from scheduling.models.pruning_models import Classifier
from scraping.prune.models import Action
from scraping.services.classify_sentence_service import get_ml_label
from scraping.services.sentence_outliers_service import add_sentence_moderation, \
    remove_sentence_not_validated_moderation, add_sentence_v2_moderation, \
    remove_sentence_not_validated_v2_moderation
from scraping.services.train_classifier_service import build_sentence_dataset, extract_label


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
        sentence_dataset = build_sentence_dataset(target)
        if not sentence_dataset:
            self.warning(f'No sentence found')
            return

        self.info(f'Got {len(sentence_dataset)} sentences for target {target}')

        nb_sentence_outliers = 0
        for sentence in sentence_dataset:
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
                human_temporal = extract_label(sentence, Classifier.Target.TEMPORAL)

                ml_confession = get_ml_label(sentence, Classifier.Target.CONFESSION)
                ml_temporal = get_ml_label(sentence, Classifier.Target.TEMPORAL)

                if human_confession != ml_confession or human_temporal != ml_temporal:
                    nb_sentence_outliers += 1
                    add_sentence_v2_moderation(sentence)
                else:
                    remove_sentence_not_validated_v2_moderation(sentence)

        self.success(f'Done! Got {nb_sentence_outliers} sentence outliers '
                     f'({nb_sentence_outliers / len(sentence_dataset) * 100:.2f} %)')
