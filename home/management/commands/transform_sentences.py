from tqdm import tqdm

from home.management.abstract_command import AbstractCommand
from home.models import ScrapingModeration, Sentence
from home.services.qualify_service import get_colored_pieces, save_sentence
from scraping.prune.models import Action
from scraping.prune.transform_sentence import get_transformer
from scraping.services.prune_scraping_service import SentenceFromDbTagInterface


class Command(AbstractCommand):
    help = "Add missing sentences and compute all embeddings"

    def handle(self, *args, **options):
        self.info(f'Getting all validated scrapings...')
        scraping_moderations = ScrapingModeration.objects\
            .filter(category=ScrapingModeration.Category.CONFESSION_HTML_PRUNED_NEW)\
            .filter(validated_at__isnull=False)\
            .all()
        for scraping_moderation in tqdm(scraping_moderations):
            scraping = scraping_moderation.scraping
            if scraping is not None and scraping.confession_html_pruned != \
                    scraping_moderation.confession_html_pruned:
                print(f"Scraping {scraping.uuid} and ScrapingModeration "
                      f"{scraping_moderation.uuid} have different pruned html. Skipping.")
                continue

            confession_html_pruned = scraping_moderation.confession_html_pruned
            colored_pieces = get_colored_pieces(confession_html_pruned,
                                                SentenceFromDbTagInterface(scraping))
            for piece in colored_pieces:
                line_without_link = piece['text_without_link']
                if piece['action'] != Action.SHOW:
                    print(f"Weird, line {line_without_link} should have action SHOW but has "
                          f"{piece['action']}. Skipping.")
                    continue
                if not piece['do_show']:
                    print(f"Weird, line {line_without_link} should be shown but is not. Skipping.")
                    continue

                save_sentence(line_without_link, scraping, scraping_moderation.validated_by,
                              Action.SHOW)

        self.info(f'Getting all sentences without embeddings...')
        sentences = Sentence.objects.filter(embedding=None).all()
        for sentence in tqdm(sentences):
            transformer = get_transformer()
            sentence.embedding = transformer.transform(sentence.line)
            sentence.transformer_name = transformer.get_name()
            sentence.save()

        self.success(f'All done!')
