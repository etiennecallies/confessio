from core.management.abstract_command import AbstractCommand
from crawling.models import CrawlingModeration
from crawling.services.crawling_moderation_service import upsert_crawling_moderation
from registry.models import WebsiteModeration
from scheduling.models import SchedulingModeration
from scheduling.services.scheduling.scheduling_moderation_service import \
    upsert_scheduling_moderation


class Command(AbstractCommand):
    help = "One shot command to migrate WebsiteModerations."

    def handle(self, *args, **options):
        self.info('Starting one shot command to migrate WebsiteModerations...')

        counter = 0
        for website_moderation in WebsiteModeration.objects.filter(category__in=[
            WebsiteModeration.Category.HOME_URL_NO_RESPONSE,
            WebsiteModeration.Category.HOME_URL_NO_CONFESSION,
            WebsiteModeration.Category.SCHEDULES_CONFLICT,
        ]):
            counter += 1
            if website_moderation.validated_at is not None:
                if website_moderation.category in [
                    WebsiteModeration.Category.HOME_URL_NO_RESPONSE,
                    WebsiteModeration.Category.HOME_URL_NO_CONFESSION,
                ]:
                    category = CrawlingModeration.Category.NO_PAGE \
                        if website_moderation.category == \
                        WebsiteModeration.Category.HOME_URL_NO_CONFESSION \
                        else CrawlingModeration.Category.NO_RESPONSE
                    crawling_moderation = upsert_crawling_moderation(
                        website_moderation.website,
                        category,
                        True)
                    crawling_moderation.validated_at = website_moderation.validated_at
                    crawling_moderation.validated_by = website_moderation.validated_by

                else:
                    scheduling_moderation = upsert_scheduling_moderation(
                        website_moderation.website,
                        SchedulingModeration.Category.SCHEDULES_CONFLICT,
                        True
                    )
                    scheduling_moderation.validated_at = website_moderation.validated_at
                    scheduling_moderation.validated_by = website_moderation.validated_by

            website_moderation_uuid = website_moderation.uuid
            website_moderation.delete()
            WebsiteModeration.history.filter(uuid=website_moderation_uuid).delete()

        self.success(f'Successfully migrated {counter} WebsiteModerations.')
