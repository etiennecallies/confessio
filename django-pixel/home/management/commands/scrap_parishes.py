from django.core.management.base import BaseCommand, CommandError

from home.models import Parish
from scrapping.search_confessions_paragraph import get_fresh_confessions_part


class Command(BaseCommand):
    help = "Launch the scrapping of all parishes"

    def handle(self, *args, **options):
        parishes = Parish.objects.all()

        for parish in parishes:
            url = parish.confession_hours_url
            confession_part = get_fresh_confessions_part(url, 'html_page')
            # poll.opened = False
            # poll.save()

            self.stdout.write(
                self.style.SUCCESS(f'Successfully got parish "{parish.uuid}"')
            )
            self.stdout.write(
                confession_part
            )
