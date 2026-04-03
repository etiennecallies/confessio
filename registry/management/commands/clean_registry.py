from core.management.abstract_cleaning_command import AbstractCleaningCommand
from registry.models import ChurchModeration, Website, WebsiteModeration


class Command(AbstractCleaningCommand):
    help = "Clean registry-related data from the database"

    def handle(self, *args, **options):
        # Church moderation
        self.info('Starting cleaning church moderation items')
        counter = 0
        for church_moderation in ChurchModeration.objects.filter(
            category=ChurchModeration.Category.LOCATION_DIFFERS,
            validated_at__isnull=True,
        ).all():
            if not church_moderation.location_desc_differs():
                church_moderation.delete()
                counter += 1
        self.success(f'Done removing {counter} church moderation items')

        # Website history
        self.delete_irrelevant_history(Website, {
            'updated_at', 'nb_recent_hits', 'is_best_diocese_hit'})

        # Website moderation history
        self.delete_irrelevant_history(WebsiteModeration, {'updated_at'})
