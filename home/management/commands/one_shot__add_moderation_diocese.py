from home.management.abstract_command import AbstractCommand
from home.models import ParsingModeration, WebsiteModeration, ParishModeration, \
    ChurchModeration, PruningModeration, ReportModeration


class Command(AbstractCommand):
    help = "One shot command to fill missinge moderation diocese."

    def handle(self, *args, **options):
        # WebsiteModeration
        counter = 0
        for website_moderation in WebsiteModeration.objects.filter(diocese__isnull=True).all():
            website_moderation.diocese = website_moderation.website.get_diocese()
            counter += 1
        self.success(f'Successfully updated {counter} website_moderations.')

        # ParsingModeration
        counter = 0
        for parsing_moderation in ParsingModeration.objects.filter(diocese__isnull=True).all():
            websites = parsing_moderation.parsing.get_websites()
            if websites:
                parsing_moderation.diocese = websites[0].get_diocese()
                counter += 1
        self.success(f'Successfully updated {counter} parsing_moderations.')

        # ParishModeration
        counter = 0
        for parish_moderation in ParishModeration.objects.filter(diocese__isnull=True).all():
            parish_moderation.diocese = parish_moderation.parish.diocese
            counter += 1
        self.success(f'Successfully updated {counter} parish_moderations.')

        # ChurchModeration
        counter = 0
        for church_moderation in ChurchModeration.objects.filter(diocese__isnull=True).all():
            church_moderation.diocese = church_moderation.church.parish.diocese
            counter += 1
        self.success(f'Successfully updated {counter} church_moderations.')

        # PruningModeration
        counter = 0
        for pruning_moderation in PruningModeration.objects.filter(diocese__isnull=True).all():
            pruning_moderation.diocese = pruning_moderation.pruning.get_diocese()
            counter += 1
        self.success(f'Successfully updated {counter} pruning_moderations.')

        # ReportModeration
        counter = 0
        for report_moderation in ReportModeration.objects.filter(diocese__isnull=True).all():
            report_moderation.diocese = report_moderation.report.website.get_diocese()
            counter += 1
        self.success(f'Successfully updated {counter} report_moderations.')
