from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs

from django.utils.timezone import make_aware

from front.models import SearchHit
from core.management.abstract_command import AbstractCommand


class Command(AbstractCommand):
    help = "Count empty search by name"

    def handle(self, *args, **options):
        self.info(f'Starting checking empty search')
        count_per_location = {}
        count_per_coordinates = {}

        now_minus_14_days = datetime.now() - timedelta(days=14)
        all_empty_searches = SearchHit.objects.filter(created_at__gt=make_aware(now_minus_14_days),
                                                      nb_websites=0).all()
        for hit in all_empty_searches:
            query = hit.query

            if query.startswith('/paroisse'):
                continue

            parsed_url = urlparse(query)
            query_params = parse_qs(parsed_url.query)

            if 'dateFilter' in query_params:
                continue

            if 'location' in query_params:
                location = query_params.get('location')[0]

                count_per_location[location] = count_per_location.get(location, 0) + 1

            if 'latitude' in query_params and 'longitude' in query_params:
                latitude = query_params.get('latitude')[0]
                longitude = query_params.get('longitude')[0]
            elif 'minLat' in query_params and 'minLng' in query_params \
                    and 'maxLat' in query_params and 'maxLng' in query_params:
                min_lat = query_params.get('minLat')[0]
                min_lng = query_params.get('minLng')[0]
                max_lat = query_params.get('maxLat')[0]
                max_lng = query_params.get('maxLng')[0]
                latitude = (float(min_lat) + float(max_lat)) / 2
                longitude = (float(min_lng) + float(max_lng)) / 2
            else:
                print(f'No coordinates in query: {query}')
                latitude = None
                longitude = None

            if latitude and longitude:
                # round latitude and longitude to 1 decimal place
                coordinates = f'{float(latitude):.1f}, {float(longitude):.1f}'
                count_per_coordinates[coordinates] = count_per_coordinates.get(coordinates, 0) + 1

        self.success('Statistics per city:')
        for location, count in sorted(count_per_location.items(), key=lambda x: x[1], reverse=True):
            self.info(f'{location}: {count}')

        self.success('And statistics per coordinates:')
        for coordinates, count in sorted(count_per_coordinates.items(), key=lambda x: x[1],
                                         reverse=True):
            self.info(f'{coordinates}: {count}')
