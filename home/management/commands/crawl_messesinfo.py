from home.management.abstract_command import AbstractCommand
from scraping.services.crawl_messesinfos_service import get_churches_on_page


class Command(AbstractCommand):
    help = "Launch the scraping of messesinfo in given network"

    def handle(self, *args, **options):
        messesinfo_network_id = "ly"
        page = 0
        total_churches = 0

        while True:
            new_churches = get_churches_on_page(messesinfo_network_id, page)
            if new_churches is None:
                self.error(f'An error occured while crawling churches in {messesinfo_network_id}')
                return

            if new_churches == 0:
                break

            total_churches += new_churches
            page += 1

        self.success(f'Successfully crawled {total_churches} churches in {messesinfo_network_id}')
