from django.core.management.base import BaseCommand, CommandError

from api.utils import parse_datetime_utc
from api.models import Station

class Command(BaseCommand):
    help = 'Set the location of a station with a given name at a given time range.'

    def add_arguments(self, parser):
        parser.add_argument('name', type=str, help='Name of the station.')
        parser.add_argument('latitude', type=float, help='Latitude of the station.')
        parser.add_argument('longitude', type=float, help='Longitude of the station.')
        parser.add_argument('--depth', type=float, help='Optional depth of the station.', default=None)
        parser.add_argument('start_time', type=str, help='Start time.')
        parser.add_argument('--end_time', type=str, help='Optional end time.', default=None)
        parser.add_argument('--comment', type=str, help='Optional comment.', default='')

    def handle(self, *args, **options):
        name = options['name']
        latitude = options['latitude']
        longitude = options['longitude']
        depth = options.get('depth', None)
        start_time = parse_datetime_utc(options['start_time'])
        end_time_str = options['end_time']
        comment = options['comment']

        end_time = None
        if end_time_str:
            end_time = parse_datetime_utc(end_time_str)

        try:
            station = Station.objects.get(name=name)
        except Station.DoesNotExist:
            raise CommandError(f'Station with name "{name}" does not exist.')

        station.set_location(
            latitude=latitude,
            longitude=longitude,
            depth=depth,
            start_time=start_time,
            end_time=end_time,
            comment=comment
        )

        self.stdout.write(self.style.SUCCESS(f'Successfully set location for station {name}'))
