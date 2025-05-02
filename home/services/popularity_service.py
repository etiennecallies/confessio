from datetime import datetime, timedelta
from uuid import UUID

from django.db.models import Q
from django.utils.timezone import make_aware
from request.models import Request

from home.models import Website, ChurchIndexEvent


def update_popularity_of_websites():
    now_minus_14_days = datetime.now() - timedelta(days=14)
    all_requests = Request.objects.filter(
        Q(path__startswith='/paroisse/')
        | Q(path__startswith='/website_churches/')
        | Q(path__startswith='/website_sources/')
        | Q(path__startswith='/website_events/'),
        time__gt=make_aware(now_minus_14_days)).all()

    count_by_website_uuids = {}
    for request in all_requests:
        request_path = request.path
        website_uuid = request_path.split('/')[2]
        try:
            website_uuid = UUID(website_uuid)
        except ValueError:
            print(f'Invalid UUID: {website_uuid}')
            continue

        count_by_website_uuids[website_uuid] = count_by_website_uuids.get(website_uuid, 0) + 1

    count_by_diocese = {}
    for website_uuid, count in count_by_website_uuids.items():
        try:
            website = Website.objects.get(uuid=website_uuid)
        except Website.DoesNotExist:
            print(f'Website not found: {website_uuid}')
            continue

        diocese = website.get_diocese()
        count_by_diocese.setdefault(diocese, {})[website] = count
        website.nb_recent_hits = count
        website.save()

    print('Setting is_best_diocese_hit to False for all websites')
    Website.objects.update(is_best_diocese_hit=False)
    print('Computing best website for each diocese')
    for diocese, count_by_website in count_by_diocese.items():
        best_website = get_best_wesbite_for_diocese(count_by_website)
        print(f'Best website for {diocese.name}: {best_website} '
              f'with count {count_by_website[best_website]}')
        best_website.is_best_diocese_hit = True
        best_website.save()


def get_best_wesbite_for_diocese(count_by_website: dict[Website, int],) -> Website:
    for website, count in sorted(count_by_website.items(), key=lambda item: item[1], reverse=True):
        if ChurchIndexEvent.objects.filter(church__parish__website=website,
                                           is_explicitely_other__isnull=True).exists():
            return website

    return max(count_by_website, key=count_by_website.get)
