import datetime
import pprint
import re
from enum import Enum
from typing import List, Dict


class HolidayZoneEnum(str, Enum):
    FR_ZONE_A = 'fr_zone_a'
    FR_ZONE_B = 'fr_zone_b'
    FR_ZONE_C = 'fr_zone_c'
    CORSICA = 'corsica'

    def __repr__(self):
        return f"'{self.value}'"


def parse_ics(ics_content: str) -> List[Dict]:
    events = []
    event_pattern = re.compile(r'BEGIN:VEVENT(.*?)END:VEVENT', re.DOTALL)

    for match in event_pattern.findall(ics_content):
        name = re.search(r'SUMMARY:(.*?)\n', match)

        if not name or not name.group(1).startswith('Vacances'):
            continue

        start_date = re.search(r'DTSTART;VALUE=DATE:(\d+)', match)
        end_date = re.search(r'DTEND;VALUE=DATE:(\d+)', match)
        location = re.search(r'LOCATION:(.*?)\n', match)

        if name and start_date and end_date and location:
            start_date = datetime.datetime.strptime(start_date.group(1), "%Y%m%d").date()
            end_date = datetime.datetime.strptime(end_date.group(1), "%Y%m%d").date()
            zones = parse_zones(location.group(1))

            events.append({
                'name': name.group(1),
                'zones': zones,
                'start_date': start_date,
                'end_date': end_date
            })

    return events


def parse_zones(location: str) -> List[HolidayZoneEnum]:
    zones = []
    if 'Zones A/B/C' in location:
        zones.append(HolidayZoneEnum.FR_ZONE_A)
        zones.append(HolidayZoneEnum.FR_ZONE_B)
        zones.append(HolidayZoneEnum.FR_ZONE_C)
    elif 'Zones A/B' in location:
        zones.append(HolidayZoneEnum.FR_ZONE_A)
        zones.append(HolidayZoneEnum.FR_ZONE_B)
    elif 'Zones B/C' in location:
        zones.append(HolidayZoneEnum.FR_ZONE_B)
        zones.append(HolidayZoneEnum.FR_ZONE_C)
    elif 'Zones A/C' in location:
        zones.append(HolidayZoneEnum.FR_ZONE_A)
        zones.append(HolidayZoneEnum.FR_ZONE_C)

    if 'Zone A' in location:
        zones.append(HolidayZoneEnum.FR_ZONE_A)
    elif 'Zone B' in location:
        zones.append(HolidayZoneEnum.FR_ZONE_B)
    elif 'Zone C' in location:
        zones.append(HolidayZoneEnum.FR_ZONE_C)

    if 'Corse' in location:
        zones.append(HolidayZoneEnum.CORSICA)
    return zones


def generate_and_print_holiday_by_zone():
    # https://www.data.gouv.fr/fr/datasets/5889d03ea3a72974cbf0d5b0/#/resources
    ics_content = """
    BEGIN:VEVENT
    DTSTAMP:20250114T124531Z
    DTSTART;VALUE=DATE:20260704
    DTEND;VALUE=DATE:20260704
    SUMMARY:Début des Vacances d'Été - Zones A/B/C
    UID:20250114T124833Z-Zone-A-B-C-Corse@data.education.gouv.fr
    LOCATION:Zones A/B/C
    DESCRIPTION:Début des Vacances d'Été - Zones A/B/C
    TRANSP:TRANSPARENT
    END:VEVENT
    BEGIN:VEVENT
    DTSTAMP:20250114T124531Z
    DTSTART;VALUE=DATE:20260514
    DTEND;VALUE=DATE:20260518
    SUMMARY:Pont de l'Ascension - Zones A/B/C
    UID:20250114T124834Z-Zone-A-B-C-Corse@data.education.gouv.fr
    LOCATION:Zones A/B/C
    DESCRIPTION:Pont de l'Ascension - Zones A/B/C
    TRANSP:TRANSPARENT
    END:VEVENT
    BEGIN:VEVENT
    DTSTAMP:20250114T124531Z
    DTSTART;VALUE=DATE:20260427
    DTEND;VALUE=DATE:20260504
    SUMMARY:Vacances de Printemps - Zone C
    UID:20250114T124835Z-Zone-A-B-C-Corse@data.education.gouv.fr
    LOCATION:Zone C
    DESCRIPTION:Vacances de Printemps - Zone C
    TRANSP:TRANSPARENT
    END:VEVENT
    BEGIN:VEVENT
    DTSTAMP:20250114T124531Z
    DTSTART;VALUE=DATE:20260420
    DTEND;VALUE=DATE:20260427
    SUMMARY:Vacances de Printemps - Zones B/C
    UID:20250114T124836Z-Zone-A-B-C-Corse@data.education.gouv.fr
    LOCATION:Zones B/C
    DESCRIPTION:Vacances de Printemps - Zones B/C
    TRANSP:TRANSPARENT
    END:VEVENT
    BEGIN:VEVENT
    DTSTAMP:20250114T124531Z
    DTSTART;VALUE=DATE:20260418
    DTEND;VALUE=DATE:20260420
    SUMMARY:Vacances de Printemps - Zones A/B/C
    UID:20250114T124837Z-Zone-A-B-C-Corse@data.education.gouv.fr
    LOCATION:Zones A/B/C
    DESCRIPTION:Vacances de Printemps - Zones A/B/C
    TRANSP:TRANSPARENT
    END:VEVENT
    BEGIN:VEVENT
    DTSTAMP:20250114T124531Z
    DTSTART;VALUE=DATE:20260411
    DTEND;VALUE=DATE:20260418
    SUMMARY:Vacances de Printemps - Zones A/B
    UID:20250114T124838Z-Zone-A-B-C-Corse@data.education.gouv.fr
    LOCATION:Zones A/B
    DESCRIPTION:Vacances de Printemps - Zones A/B
    TRANSP:TRANSPARENT
    END:VEVENT
    BEGIN:VEVENT
    DTSTAMP:20250114T124531Z
    DTSTART;VALUE=DATE:20260404
    DTEND;VALUE=DATE:20260411
    SUMMARY:Vacances de Printemps - Zone A
    UID:20250114T124839Z-Zone-A-B-C-Corse@data.education.gouv.fr
    LOCATION:Zone A
    DESCRIPTION:Vacances de Printemps - Zone A
    TRANSP:TRANSPARENT
    END:VEVENT
    BEGIN:VEVENT
    DTSTAMP:20250114T124531Z
    DTSTART;VALUE=DATE:20260302
    DTEND;VALUE=DATE:20260309
    SUMMARY:Vacances d'Hiver - Zone C
    UID:20250114T124840Z-Zone-A-B-C-Corse@data.education.gouv.fr
    LOCATION:Zone C
    DESCRIPTION:Vacances d'Hiver - Zone C
    TRANSP:TRANSPARENT
    END:VEVENT
    BEGIN:VEVENT
    DTSTAMP:20250114T124531Z
    DTSTART;VALUE=DATE:20260223
    DTEND;VALUE=DATE:20260302
    SUMMARY:Vacances d'Hiver - Zones B/C
    UID:20250114T124841Z-Zone-A-B-C-Corse@data.education.gouv.fr
    LOCATION:Zones B/C
    DESCRIPTION:Vacances d'Hiver - Zones B/C
    TRANSP:TRANSPARENT
    END:VEVENT
    BEGIN:VEVENT
    DTSTAMP:20250114T124531Z
    DTSTART;VALUE=DATE:20260221
    DTEND;VALUE=DATE:20260223
    SUMMARY:Vacances d'Hiver - Zones A/B/C
    UID:20250114T124842Z-Zone-A-B-C-Corse@data.education.gouv.fr
    LOCATION:Zones A/B/C
    DESCRIPTION:Vacances d'Hiver - Zones A/B/C
    TRANSP:TRANSPARENT
    END:VEVENT
    BEGIN:VEVENT
    DTSTAMP:20250114T124531Z
    DTSTART;VALUE=DATE:20260214
    DTEND;VALUE=DATE:20260221
    SUMMARY:Vacances d'Hiver - Zones A/B
    UID:20250114T124843Z-Zone-A-B-C-Corse@data.education.gouv.fr
    LOCATION:Zones A/B
    DESCRIPTION:Vacances d'Hiver - Zones A/B
    TRANSP:TRANSPARENT
    END:VEVENT
    BEGIN:VEVENT
    DTSTAMP:20250114T124531Z
    DTSTART;VALUE=DATE:20260207
    DTEND;VALUE=DATE:20260214
    SUMMARY:Vacances d'Hiver - Zone A
    UID:20250114T124844Z-Zone-A-B-C-Corse@data.education.gouv.fr
    LOCATION:Zone A
    DESCRIPTION:Vacances d'Hiver - Zone A
    TRANSP:TRANSPARENT
    END:VEVENT
    BEGIN:VEVENT
    DTSTAMP:20250114T124531Z
    DTSTART;VALUE=DATE:20251220
    DTEND;VALUE=DATE:20260105
    SUMMARY:Vacances de Noël - Zones A/B/C
    UID:20250114T124845Z-Zone-A-B-C-Corse@data.education.gouv.fr
    LOCATION:Zones A/B/C
    DESCRIPTION:Vacances de Noël - Zones A/B/C
    TRANSP:TRANSPARENT
    END:VEVENT
    BEGIN:VEVENT
    DTSTAMP:20250114T124531Z
    DTSTART;VALUE=DATE:20251018
    DTEND;VALUE=DATE:20251103
    SUMMARY:Vacances de la Toussaint - Zones A/B/C
    UID:20250114T124846Z-Zone-A-B-C-Corse@data.education.gouv.fr
    LOCATION:Zones A/B/C
    DESCRIPTION:Vacances de la Toussaint - Zones A/B/C
    TRANSP:TRANSPARENT
    END:VEVENT
    BEGIN:VEVENT
    DTSTAMP:20250114T124531Z
    DTSTART;VALUE=DATE:20250829
    DTEND;VALUE=DATE:20250901
    SUMMARY:Vacances d'Été(prérentrée Enseignants) - Zones A/B/C
    UID:20250114T124847Z-Zone-A-B-C-Corse@data.education.gouv.fr
    LOCATION:Zones A/B/C
    DESCRIPTION:Vacances d'Été(prérentrée Enseignants) - Zones A/B/C
    TRANSP:TRANSPARENT
    END:VEVENT
    BEGIN:VEVENT
    DTSTAMP:20250114T124531Z
    DTSTART;VALUE=DATE:20250705
    DTEND;VALUE=DATE:20250901
    SUMMARY:Vacances d'Été - Zones A/B/C
    UID:20250114T124848Z-Zone-A-B-C-Corse@data.education.gouv.fr
    LOCATION:Zones A/B/C
    DESCRIPTION:Vacances d'Été - Zones A/B/C
    TRANSP:TRANSPARENT
    END:VEVENT
    BEGIN:VEVENT
    DTSTAMP:20250114T124531Z
    DTSTART;VALUE=DATE:20250705
    DTEND;VALUE=DATE:20250705
    SUMMARY:Début des Vacances d'Été - Corse
    UID:20250114T124849Z-Zone-A-B-C-Corse@data.education.gouv.fr
    LOCATION:Corse
    DESCRIPTION:Début des Vacances d'Été - Corse
    TRANSP:TRANSPARENT
    END:VEVENT
    BEGIN:VEVENT
    DTSTAMP:20250114T124531Z
    DTSTART;VALUE=DATE:20250609
    DTEND;VALUE=DATE:20250609
    SUMMARY:Lundi de Pentecôte - Corse
    UID:20250114T124850Z-Zone-A-B-C-Corse@data.education.gouv.fr
    LOCATION:Corse
    DESCRIPTION:Lundi de Pentecôte - Corse
    TRANSP:TRANSPARENT
    END:VEVENT
    BEGIN:VEVENT
    DTSTAMP:20250114T124531Z
    DTSTART;VALUE=DATE:20250529
    DTEND;VALUE=DATE:20250602
    SUMMARY:Pont de l'Ascension - Zones A/B/C - Corse
    UID:20250114T124851Z-Zone-A-B-C-Corse@data.education.gouv.fr
    LOCATION:Zones A/B/C - Corse
    DESCRIPTION:Pont de l'Ascension - Zones A/B/C - Corse
    TRANSP:TRANSPARENT
    END:VEVENT
    BEGIN:VEVENT
    DTSTAMP:20250114T124531Z
    DTSTART;VALUE=DATE:20250428
    DTEND;VALUE=DATE:20250505
    SUMMARY:Vacances de Printemps - Zone A
    UID:20250114T124852Z-Zone-A-B-C-Corse@data.education.gouv.fr
    LOCATION:Zone A
    DESCRIPTION:Vacances de Printemps - Zone A
    TRANSP:TRANSPARENT
    END:VEVENT
    BEGIN:VEVENT
    DTSTAMP:20250114T124531Z
    DTSTART;VALUE=DATE:20250422
    DTEND;VALUE=DATE:20250428
    SUMMARY:Vacances de Printemps - Zones A/C - Corse
    UID:20250114T124853Z-Zone-A-B-C-Corse@data.education.gouv.fr
    LOCATION:Zones A/C - Corse
    DESCRIPTION:Vacances de Printemps - Zones A/C - Corse
    TRANSP:TRANSPARENT
    END:VEVENT
    BEGIN:VEVENT
    DTSTAMP:20250114T124531Z
    DTSTART;VALUE=DATE:20250419
    DTEND;VALUE=DATE:20250422
    SUMMARY:Vacances de Printemps - Zones A/B/C - Corse
    UID:20250114T124854Z-Zone-A-B-C-Corse@data.education.gouv.fr
    LOCATION:Zones A/B/C - Corse
    DESCRIPTION:Vacances de Printemps - Zones A/B/C - Corse
    TRANSP:TRANSPARENT
    END:VEVENT
    BEGIN:VEVENT
    DTSTAMP:20250114T124531Z
    DTSTART;VALUE=DATE:20250412
    DTEND;VALUE=DATE:20250419
    SUMMARY:Vacances de Printemps - Zones B/C - Corse
    UID:20250114T124855Z-Zone-A-B-C-Corse@data.education.gouv.fr
    LOCATION:Zones B/C - Corse
    DESCRIPTION:Vacances de Printemps - Zones B/C - Corse
    TRANSP:TRANSPARENT
    END:VEVENT
    BEGIN:VEVENT
    DTSTAMP:20250114T124531Z
    DTSTART;VALUE=DATE:20250405
    DTEND;VALUE=DATE:20250412
    SUMMARY:Vacances de Printemps - Zone B
    UID:20250114T124856Z-Zone-A-B-C-Corse@data.education.gouv.fr
    LOCATION:Zone B
    DESCRIPTION:Vacances de Printemps - Zone B
    TRANSP:TRANSPARENT
    END:VEVENT
    BEGIN:VEVENT
    DTSTAMP:20250114T124531Z
    DTSTART;VALUE=DATE:20250303
    DTEND;VALUE=DATE:20250310
    SUMMARY:Vacances d'Hiver - Zone A
    UID:20250114T124857Z-Zone-A-B-C-Corse@data.education.gouv.fr
    LOCATION:Zone A
    DESCRIPTION:Vacances d'Hiver - Zone A
    TRANSP:TRANSPARENT
    END:VEVENT
    BEGIN:VEVENT
    DTSTAMP:20250114T124531Z
    DTSTART;VALUE=DATE:20250224
    DTEND;VALUE=DATE:20250303
    SUMMARY:Vacances d'Hiver - Zones A/C - Corse
    UID:20250114T124858Z-Zone-A-B-C-Corse@data.education.gouv.fr
    LOCATION:Zones A/C - Corse
    DESCRIPTION:Vacances d'Hiver - Zones A/C - Corse
    TRANSP:TRANSPARENT
    END:VEVENT
    BEGIN:VEVENT
    DTSTAMP:20250114T124531Z
    DTSTART;VALUE=DATE:20250222
    DTEND;VALUE=DATE:20250224
    SUMMARY:Vacances d'Hiver - Zones A/B/C - Corse
    UID:20250114T124859Z-Zone-A-B-C-Corse@data.education.gouv.fr
    LOCATION:Zones A/B/C - Corse
    DESCRIPTION:Vacances d'Hiver - Zones A/B/C - Corse
    TRANSP:TRANSPARENT
    END:VEVENT
    BEGIN:VEVENT
    DTSTAMP:20250114T124531Z
    DTSTART;VALUE=DATE:20250215
    DTEND;VALUE=DATE:20250222
    SUMMARY:Vacances d'Hiver - Zones B/C - Corse
    UID:20250114T124900Z-Zone-A-B-C-Corse@data.education.gouv.fr
    LOCATION:Zones B/C - Corse
    DESCRIPTION:Vacances d'Hiver - Zones B/C - Corse
    TRANSP:TRANSPARENT
    END:VEVENT
    BEGIN:VEVENT
    DTSTAMP:20250114T124531Z
    DTSTART;VALUE=DATE:20250208
    DTEND;VALUE=DATE:20250215
    SUMMARY:Vacances d'Hiver - Zone B
    UID:20250114T124901Z-Zone-A-B-C-Corse@data.education.gouv.fr
    LOCATION:Zone B
    DESCRIPTION:Vacances d'Hiver - Zone B
    TRANSP:TRANSPARENT
    END:VEVENT
    BEGIN:VEVENT
    DTSTAMP:20250114T124531Z
    DTSTART;VALUE=DATE:20241221
    DTEND;VALUE=DATE:20250106
    SUMMARY:Vacances de Noël - Zones A/B/C - Corse
    UID:20250114T124902Z-Zone-A-B-C-Corse@data.education.gouv.fr
    LOCATION:Zones A/B/C - Corse
    DESCRIPTION:Vacances de Noël - Zones A/B/C - Corse
    TRANSP:TRANSPARENT
    END:VEVENT
    BEGIN:VEVENT
    DTSTAMP:20250114T124531Z
    DTSTART;VALUE=DATE:20241019
    DTEND;VALUE=DATE:20241104
    SUMMARY:Vacances de la Toussaint - Zones A/B/C - Corse
    UID:20250114T124903Z-Zone-A-B-C-Corse@data.education.gouv.fr
    LOCATION:Zones A/B/C - Corse
    DESCRIPTION:Vacances de la Toussaint - Zones A/B/C - Corse
    TRANSP:TRANSPARENT
    END:VEVENT
    BEGIN:VEVENT
    """

    holiday_by_zone = {
        HolidayZoneEnum.FR_ZONE_A: {},
        HolidayZoneEnum.FR_ZONE_B: {},
        HolidayZoneEnum.FR_ZONE_C: {},
        HolidayZoneEnum.CORSICA: {},
    }

    for item in parse_ics(ics_content):
        year = item['start_date'].year
        for zone in item['zones']:
            holiday_by_zone[zone].setdefault(year, []).append((item['start_date'],
                                                               item['end_date']))
    for zone, years in holiday_by_zone.items():
        for year, periods in years.items():
            new_periods = []
            last_end = None
            for start, end in sorted(periods):
                if last_end is not None and start <= last_end:
                    new_periods[-1] = (new_periods[-1][0], end)
                else:
                    new_periods.append((start, end))
                last_end = end
            holiday_by_zone[zone][year] = new_periods

    print(pprint.pformat(holiday_by_zone))


HOLIDAY_BY_ZONE = {
    'corsica': {2024: [(datetime.date(2024, 10, 19), datetime.date(2024, 11, 4)),
                       (datetime.date(2024, 12, 21), datetime.date(2025, 1, 6))],
                2025: [(datetime.date(2025, 2, 15), datetime.date(2025, 3, 3)),
                       (datetime.date(2025, 4, 12), datetime.date(2025, 4, 28))]},
    'fr_zone_a': {2024: [(datetime.date(2024, 10, 19), datetime.date(2024, 11, 4)),
                         (datetime.date(2024, 12, 21), datetime.date(2025, 1, 6))],
                  2025: [(datetime.date(2025, 2, 22), datetime.date(2025, 3, 10)),
                         (datetime.date(2025, 4, 19), datetime.date(2025, 5, 5)),
                         (datetime.date(2025, 7, 5), datetime.date(2025, 9, 1)),
                         (datetime.date(2025, 10, 18), datetime.date(2025, 11, 3)),
                         (datetime.date(2025, 12, 20), datetime.date(2026, 1, 5))],
                  2026: [(datetime.date(2026, 2, 7), datetime.date(2026, 2, 23)),
                         (datetime.date(2026, 4, 4), datetime.date(2026, 4, 20))]},
    'fr_zone_b': {2024: [(datetime.date(2024, 10, 19), datetime.date(2024, 11, 4)),
                         (datetime.date(2024, 12, 21), datetime.date(2025, 1, 6))],
                  2025: [(datetime.date(2025, 2, 8), datetime.date(2025, 2, 24)),
                         (datetime.date(2025, 4, 5), datetime.date(2025, 4, 22)),
                         (datetime.date(2025, 7, 5), datetime.date(2025, 9, 1)),
                         (datetime.date(2025, 10, 18), datetime.date(2025, 11, 3)),
                         (datetime.date(2025, 12, 20), datetime.date(2026, 1, 5))],
                  2026: [(datetime.date(2026, 2, 14), datetime.date(2026, 3, 2)),
                         (datetime.date(2026, 4, 11),
                          datetime.date(2026, 4, 27))]},
    'fr_zone_c': {2024: [(datetime.date(2024, 10, 19), datetime.date(2024, 11, 4)),
                         (datetime.date(2024, 12, 21), datetime.date(2025, 1, 6))],
                  2025: [(datetime.date(2025, 2, 15), datetime.date(2025, 3, 3)),
                         (datetime.date(2025, 4, 12), datetime.date(2025, 4, 28)),
                         (datetime.date(2025, 7, 5), datetime.date(2025, 9, 1)),
                         (datetime.date(2025, 10, 18), datetime.date(2025, 11, 3)),
                         (datetime.date(2025, 12, 20), datetime.date(2026, 1, 5))],
                  2026: [(datetime.date(2026, 2, 21), datetime.date(2026, 3, 9)),
                         (datetime.date(2026, 4, 18), datetime.date(2026, 5, 4))]}}


if __name__ == '__main__':
    generate_and_print_holiday_by_zone()
