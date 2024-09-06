from django.db.models import Q

from home.management.abstract_command import AbstractCommand
from home.models import Pruning
from scraping.services.parse_pruning_service import parse_pruning_for_website


class Command(AbstractCommand):
    help = "Parse one or more prunings for one or more websites"

    def add_arguments(self, parser):
        parser.add_argument('-n', '--name', help='name of website to parse')
        parser.add_argument('-p', '--pruning-uuid', action='append',
                            default=[], help='uuid of pruning to parse (can be repeated)')
        parser.add_argument('-m', '--max', help='max number of parsing to do', type=int)

    def handle(self, *args, **options):
        query = Q(scrapings__page__website__is_active=True)
        if options['pruning_uuid']:
            query &= Q(uuid__in=options['pruning_uuid'])
        if options['name']:
            query &= Q(scrapings__page__website__name__contains=options['name'])
        prunings = Pruning.objects.filter(query).distinct()

        counter = 0
        max_parsings = options['max'] or None
        for pruning in prunings:
            for scraping in pruning.scrapings.all():
                if max_parsings and counter >= max_parsings:
                    break

                website = scraping.page.website
                self.info(f'Parsing {pruning.uuid} for website {website.name}')
                parse_pruning_for_website(pruning, website)
                counter += 1

        self.success(f'Successfully parsed {counter} pruning-websites')