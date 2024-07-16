from home.management.abstract_command import AbstractCommand
from home.models import Diocese
from sourcing.services.crawl_messesinfos_service import get_parishes_and_churches
from sourcing.services.sync_churches_service import MessesinfoChurchRetriever, sync_churches
from sourcing.services.sync_parishes_service import sync_parishes, MessesinfoParishRetriever


class Command(AbstractCommand):
    help = "Launch the scraping of messesinfo in given network"

    def add_arguments(self, parser):
        parser.add_argument('messesinfo_network_id', type=str,
                            help='Two letters code of messesinfo network_id (diocese)')
        parser.add_argument('--allow-no-url', action="store_true",
                            help='do not ignore parishes without url')

    def handle(self, *args, **options):
        messesinfo_network_id = options['messesinfo_network_id']
        try:
            diocese = Diocese.objects.get(messesinfo_network_id=messesinfo_network_id)
        except Diocese.DoesNotExist:
            self.error(f'No diocese for network_id {messesinfo_network_id}')
            return

        self.info(f'Starting crawling messesinfo parishes and churches in '
                  f'{messesinfo_network_id}')
        parishes, churches = get_parishes_and_churches(messesinfo_network_id, diocese)
        self.info(f'Successfully crawled {len(parishes)} parishes and {len(churches)} churches')
        self.info(f'Starting synchronization of parishes')
        sync_parishes(parishes, diocese, MessesinfoParishRetriever(),
                      allow_no_url=options['allow_no_url'])
        self.success(f'Parish synchronization done!')
        self.info(f'Starting synchronization of churches')
        sync_churches(churches, diocese, MessesinfoChurchRetriever(),
                      allow_no_url=options['allow_no_url'])
        self.success(f'Church synchronization done!')