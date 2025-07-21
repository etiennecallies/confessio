from home.management.abstract_command import AbstractCommand
from home.models import Website
from scraping.services.parse_pruning_service import check_website_parsing_relations


class Command(AbstractCommand):
    help = "One shot command to check parsing website."

    def handle(self, *args, **options):
        counter = 0
        for website in Website.objects.filter(enabled_for_crawling=True).all():
            counter += 1
            if not check_website_parsing_relations(website):
                self.warning(f'Website {website.name} ({website.uuid}) has a parsing issue. '
                             f'enabled_for_crawling: {website.enabled_for_crawling}, '
                             f'unreliability_reason: {website.unreliability_reason}, '
                             f'is_active: {website.is_active}')

                for page in website.pages.all():
                    scraping = page.scraping
                    for pruning in scraping.prunings.all():
                        parsing = pruning.get_parsing(website)
                        if parsing:
                            self.warning(f'  Parsing {parsing.uuid} for pruning {pruning.uuid} '
                                         f'of scraping {scraping.uuid} of page {page.uuid} '
                                         f'(pruned_indices: {pruning.pruned_indices})')
                break

        self.success(f'Checked {counter} websites.')
