from home.management.abstract_command import AbstractCommand
from home.models import Pruning
from scraping.services.parse_pruning_service import parse_pruning_for_website


class Command(AbstractCommand):
    help = "Parse one or more prunings for all websites"

    def add_arguments(self, parser):
        parser.add_argument('-p', '--pruning-uuid', action='append',
                            default=[], help='uuid of pruning to parse (can be repeated)')

    def handle(self, *args, **options):
        if options['pruning_uuid']:
            prunings = Pruning.objects.filter(scrapings__page__website__is_active=True,
                                              uuid__in=options['pruning_uuid']).distinct()
        else:
            prunings = Pruning.objects.filter(scrapings__page__website__is_active=True).distinct()

        counter = 0
        for pruning in prunings:
            for scraping in pruning.scrapings.all():
                website = scraping.page.website
                self.info(f'Parsing {pruning.uuid} for website {website.name}')
                parse_pruning_for_website(pruning, website)
                counter += 1

        self.success(f'Successfully parsed {counter} pruning-websites')
