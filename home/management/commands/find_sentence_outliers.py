from home.management.abstract_command import AbstractCommand
from scraping.prune.models import Action
from scraping.services.classify_sentence_service import classify_line
from scraping.services.sentence_outliers_service import add_sentence_moderation, \
    remove_sentence_not_validated_moderation
from scraping.services.train_classifier_service import build_sentence_dataset


class Command(AbstractCommand):
    help = ("Launch the inference of latest classifier and find mismatch between prediction and "
            "human label")

    def handle(self, *args, **options):
        self.info(f'Building sentence dataset...')
        sentence_dataset = build_sentence_dataset()
        if not sentence_dataset:
            self.warning(f'No sentence found')
            return

        self.info(f'Got {len(sentence_dataset)} sentences')

        nb_sentence_outliers = 0
        for sentence in sentence_dataset:
            human_action = Action(sentence.action)
            action, classifier, embedding, transformer = classify_line(sentence.line)
            if action != human_action:
                self.warning(f'Got {action} vs human label {human_action} '
                             f'on line "{sentence.line}"')
                nb_sentence_outliers += 1
                add_sentence_moderation(sentence, other_action=action)
            else:
                remove_sentence_not_validated_moderation(sentence)

        self.success(f'Done! Got {nb_sentence_outliers} sentence outliers '
                     f'({nb_sentence_outliers/len(sentence_dataset) * 100:.2f} %)')
