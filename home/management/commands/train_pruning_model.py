from django.core.management import call_command

from home.management.abstract_command import AbstractCommand
from home.models import Classifier, Sentence
from scraping.prune.transform_sentence import get_transformer
from scraping.services.classify_sentence_service import classify_line, get_classifier
from scraping.services.train_classifier_service import train_classifier, build_sentence_dataset
from scraping.utils.stat_utils import is_significantly_different


class Command(AbstractCommand):
    help = "Launch the training of machine learning model to guess action of Sentence"

    def add_arguments(self, parser):
        parser.add_argument('-t', '--test-on-line', help='test latest classifier on given line')
        parser.add_argument('-a', '--automatic', action='store_true',
                            help='automatic training triggered in nightly job')

    def handle(self, *args, **options):
        if options['test_on_line']:
            action, classifier, embedding, transformer = classify_line(options['test_on_line'])
            self.success(f'Successfully got action {action}')
            return

        if options['automatic']:
            last_training_at = Classifier.objects.latest('created_at').created_at
            self.info(f'Last training was at {last_training_at}')

            last_sentence_at = Sentence.objects.filter(updated_by__isnull=False)\
                .latest('updated_at').updated_at
            self.info(f'Last human-changed sentence updated at {last_sentence_at}')

            if last_training_at > last_sentence_at:
                self.info(f'No need to retrain model')
                return

        self.info(f'Building sentence dataset...')
        sentence_dataset = build_sentence_dataset()
        self.info(f'Got {len(sentence_dataset)} sentences')

        self.info(f'Training model ...')
        classifier = train_classifier(sentence_dataset)
        self.success(f'Successfully trained model with accuracy {classifier.accuracy}, '
                     f'with test size {classifier.test_size}')

        if options['automatic']:
            transformer = get_transformer()
            production_classifier = get_classifier(transformer)
            self.info(f'Production model accuracy: {production_classifier.accuracy}, '
                      f'test size: {production_classifier.test_size}')

            if classifier.accuracy > production_classifier.accuracy and \
                is_significantly_different(classifier.accuracy, production_classifier.accuracy,
                                           classifier.test_size, production_classifier.test_size):
                self.success(f'New model is significantly better than production model')
                classifier.status = classifier.Status.PROD
                classifier.save()

                self.info(f'Launching find_sentence_outliers command...')
                call_command('find_sentence_outliers')
                self.success(f'End of find_sentence_outliers command.')
            else:
                self.info(f'New model is not significantly better than production model')

        if classifier.status == classifier.Status.DRAFT:
            self.warning(f'WARNING: Trained model is still in draft status. '
                         f'You shall set it to prod in admin interface.')
        else:
            self.success(f'Model has now status {classifier.status}')
