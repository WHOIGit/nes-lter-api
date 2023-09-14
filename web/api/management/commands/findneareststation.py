from django.core.management.base import BaseCommand, CommandError

from api.models import Station
from api.queries import find_nearest, parse_datetime

class Command(BaseCommand):
    help = "Set station location (name)"

    def add_arguments(self, parser):
        parser.add_argument("latitude", type=float)
        parser.add_argument("longitude", type=float)
        parser.add_argument('time', type=str, default=None)

    def handle(self, *args, **options):
        given_time = parse_datetime(options["time"])
        if not given_time:
            raise CommandError(f"Invalid time {options['time']}")
        nearest = find_nearest(Station, options["latitude"], options["longitude"], given_time)
        print(nearest)
