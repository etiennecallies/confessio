from tqdm import tqdm

from home.management.abstract_command import AbstractCommand
from scheduling.utils.list_utils import chunk_list
from scheduling.models.pruning_models import Classifier
from scraping.services.classify_sentence_service import get_sentences_with_wrong_classifier, \
    classify_existing_sentences
from scraping.services.train_classifier_service import set_label


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
        for sentence_chunk in tqdm(list(chunk_list(sentences, 100))):
            ml_labels, classifier = classify_existing_sentences(sentence_chunk, target)
            assert len(ml_labels) == len(sentence_chunk)
            for i, ml_label in enumerate(ml_labels):
                sentence = sentence_chunk[i]
                set_label(sentence, ml_label, classifier)
                sentence.save()
                counter += 1
        self.success(f'Finished reclassifying {counter} sentences for target {target}')
