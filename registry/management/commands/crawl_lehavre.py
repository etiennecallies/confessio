from core.management.abstract_command import AbstractCommand
from sourcing.services.crawl_lehavre_service import get_churches_on_lehavre


class Command(AbstractCommand):
    help = "Crawl Le Havre diocese web site that contains parishes and churches"

    def handle(self, *args, **options):
        self.info(f'Starting crawling Le Havre parishes and churches')

        page = 1
        total_parishes = 0
        total_churches = 0

        while True:
            result = get_churches_on_lehavre(page)
            if result is None:
                print(f'nothing on page {page}')
                break

            nb_parishes, nb_churches = result
            total_parishes += nb_parishes
            total_churches += nb_churches
            page += 1

        self.success(f'Successfully crawled {total_parishes} parishes '
                     f'and {total_churches} churches on Le Havre diocese website')
