from tqdm import tqdm

from home.management.abstract_command import AbstractCommand
from home.models import Classifier
from scraping.services.classify_sentence_service import get_sentences_with_wrong_classifier, \
    get_ml_label


class Command(AbstractCommand):
    help = "Reclassify all sentences with the latest model, given target"

    def add_arguments(self, parser):
        parser.add_argument('-t', '--target', type=Classifier.Target,
                            choices=list(Classifier.Target), help='Target of the classifier')

    def handle(self, *args, **options):
        target = options['target']
        if target:
            targets = [target]
        else:
            targets = [t for t in Classifier.Target]

        for target in targets:
            self.reclassify_for_target(target)

    def reclassify_for_target(self, target: Classifier.Target):
        self.info(f'Reclassifying all sentences with the latest model for target {target}')
        sentences = get_sentences_with_wrong_classifier(target)
        counter = 0
        for sentence in tqdm(sentences):
            get_ml_label(sentence, target)
            counter += 1
        self.success(f'Finished reclassifying {counter} sentences for target {target}')
