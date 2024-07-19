from home.management.abstract_command import AbstractCommand
from scraping.services.build_sentence_dataset_service import build_sentence_dataset
from scraping.services.train_classifier_service import train_classifier


class Command(AbstractCommand):
    help = "Launch the training of machine learning model to guess action of Sentence"

    def handle(self, *args, **options):
        self.info(f'Building sentence dataset...')
        sentence_dataset = build_sentence_dataset()
        self.info(f'Got {len(sentence_dataset)} sentences')
        self.info(f'Training model ...')
        classifier = train_classifier(sentence_dataset)
        self.success(f'Successfully trained model with accuracy {classifier.accuracy}')
