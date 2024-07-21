from home.management.abstract_command import AbstractCommand
from scraping.services.classify_sentence_service import classify_line
from scraping.services.train_classifier_service import train_classifier, build_sentence_dataset


class Command(AbstractCommand):
    help = "Launch the training of machine learning model to guess action of Sentence"

    def add_arguments(self, parser):
        parser.add_argument('-t', '--test-on-line', help='test latest classifier on given line')

    def handle(self, *args, **options):
        if options['test_on_line']:
            action, classifier, embedding, transformer = classify_line(options['test_on_line'])
            self.success(f'Successfully got action {action}')
            return

        self.info(f'Building sentence dataset...')
        sentence_dataset = build_sentence_dataset()
        self.info(f'Got {len(sentence_dataset)} sentences')
        self.info(f'Training model ...')
        classifier = train_classifier(sentence_dataset)
        self.success(f'Successfully trained model with accuracy {classifier.accuracy}')
        if classifier.status == classifier.Status.DRAFT:
            self.warning(f'WARNING: Trained model is still in draft status. '
                         f'You shall set it to prod in admin interface.')
