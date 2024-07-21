from tqdm import tqdm

from home.management.abstract_command import AbstractCommand
from home.models import ScrapingModeration, Sentence
from home.services.qualify_service import get_colored_pieces, save_sentence
from scraping.prune.models import Action
from scraping.prune.transform_sentence import get_transformer
from scraping.services.prune_scraping_service import SentenceFromDbTagInterface, \
    prune_scraping_and_save, add_necessary_moderation


class Command(AbstractCommand):
    help = "Add missing sentences and compute all embeddings"

    def handle(self, *args, **options):
        self.info(f'Deleting all ScrapingModeration without scraping...')
        ScrapingModeration.objects \
            .filter(scraping__isnull=True) \
            .delete()

        self.info(f'Getting all validated scrapings...')
        scraping_moderations = ScrapingModeration.objects\
            .filter(category=ScrapingModeration.Category.CONFESSION_HTML_PRUNED_NEW)\
            .filter(validated_at__isnull=False)\
            .all()
        for scraping_moderation in tqdm(scraping_moderations):
            scraping = scraping_moderation.scraping
            assert scraping is not None, "ScrapingModeration should have a scraping"

            if scraping.confession_html_pruned != scraping_moderation.confession_html_pruned:
                self.warning(f"Scraping {scraping.uuid} and ScrapingModeration "
                             f"{scraping_moderation.uuid} have different pruned html."
                             f"Re-adding moderation.")
                add_necessary_moderation(scraping)
                continue

            confession_html_pruned = scraping_moderation.confession_html_pruned
            colored_pieces = get_colored_pieces(confession_html_pruned,
                                                SentenceFromDbTagInterface(scraping))
            needs_pruning = False
            for piece in colored_pieces:
                line_without_link = piece['text_without_link']
                if piece['action'] != Action.SHOW:
                    self.warning(f"Weird, line {line_without_link} should have action SHOW but has "
                                 f"{piece['action']}. Related scraping will be re-pruned.")
                    needs_pruning = True
                    continue
                if not piece['do_show']:
                    self.warning(f"Weird, line {line_without_link} should be shown but is not."
                                 f" Related scraping will be re-pruned.")
                    needs_pruning = True
                    continue

                save_sentence(line_without_link, scraping, scraping_moderation.validated_by,
                              Action.SHOW)
            if needs_pruning:
                prune_scraping_and_save(scraping)

        self.info(f'Getting all sentences without embeddings...')
        sentences = Sentence.objects.filter(embedding=None).all()
        for sentence in tqdm(sentences):
            transformer = get_transformer()
            sentence.embedding = transformer.transform(sentence.line)
            sentence.transformer_name = transformer.get_name()
            sentence.save()

        self.success(f'All done!')
