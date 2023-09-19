from django.core.management.base import BaseCommand, CommandError

from api.utils import parse_datetime_utc
from api.models import Station

class Command(BaseCommand):
    help = "Find nearest station"

    def add_arguments(self, parser):
        parser.add_argument("latitude", type=float)
        parser.add_argument("longitude", type=float)
        parser.add_argument('time', type=str, default=None)

    def handle(self, *args, **options):
        given_time = parse_datetime_utc(options["time"])
        nearest, distance = Station.nearest_station(options["latitude"], options["longitude"], given_time)
        if nearest is None:
            self.stderr.write(self.style.ERROR(f'No stations found'))
            return
        self.stdout.write(self.style.SUCCESS(f'Nearest station is {nearest.name} at {distance} meters'))
