from django.db.models import Q

from home.management.abstract_command import AbstractCommand
from home.models import Pruning
from scraping.services.parse_pruning_service import parse_pruning_for_website


class Command(AbstractCommand):
    help = "Parse one or more prunings for one or more websites"

    def add_arguments(self, parser):
        parser.add_argument('-n', '--name', help='name of website to parse')
        parser.add_argument('-d', '--diocese', help='diocese messesinfo_network_id to parse')
        parser.add_argument('-p', '--pruning-uuid', action='append',
                            default=[], help='uuid of pruning to parse (can be repeated)')
        parser.add_argument('-m', '--max', help='max number of parsing to do', type=int)
        parser.add_argument('-f', '--force-parse', action="store_true",
                            help='force parsing even if already parsed')
        parser.add_argument('-e', '--existing', action="store_true",
                            help='re-parse existing parsings')

    def handle(self, *args, **options):
        query = Q(scrapings__temp_page__website__is_active=True,
                  scrapings__temp_page__website__unreliability_reason__exact='',
                  pruned_indices__len__gt=0)
        if options['pruning_uuid']:
            query &= Q(uuid__in=options['pruning_uuid'])
        elif options['existing']:
            query &= Q(parsings__isnull=False)
        else:
            query &= Q(scrapings__isnull=False)

        if options['name']:
            query &= Q(scrapings__temp_page__website__name__contains=options['name'])
        if options['diocese']:
            d = options['diocese']
            query &= Q(
                scrapings__temp_page__website__parishes__diocese__messesinfo_network_id__exact=d)

        prunings = Pruning.objects.filter(query).distinct()

        counter = 0
        max_parsings = options['max'] or None
        for pruning in prunings:
            for scraping in pruning.scrapings.all():
                if max_parsings and counter >= max_parsings:
                    break

                website = scraping.temp_page.website
                self.info(f'Pruning {pruning.uuid} for website {website.name}')
                parse_pruning_for_website(pruning, website, options['force_parse'])
                counter += 1

        self.success(f'Successfully parsed {counter} pruning-websites')
