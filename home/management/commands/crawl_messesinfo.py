from django.core.management.base import BaseCommand

from scraping.services.crawl_messesinfos_service import get_churches_on_page


class Command(BaseCommand):
    help = "Launch the scraping of messesinfo in given network"

    def handle(self, *args, **options):
        network_id = "DIOCESE:LY"
        page = 0
        total_churches = 0

        while True:
            new_churches = get_churches_on_page(network_id, page)
            if new_churches is None:
                self.stdout.write(
                    self.style.ERROR(f'An error occured while crawling churches in {network_id}')
                )
                return

            if new_churches == 0:
                break

            total_churches += new_churches
            page += 1

        self.stdout.write(
            self.style.SUCCESS(f'Successfully crawled {total_churches} churches in {network_id}')
        )
