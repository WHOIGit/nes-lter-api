from django.core.management.base import BaseCommand, CommandError

from dateutil import parser

from api.models import Station, find_nearest

class Command(BaseCommand):
    help = "Set station location (name)"

    def add_arguments(self, parser):
        parser.add_argument("latitude", type=float)
        parser.add_argument("longitude", type=float)
        parser.add_argument('time', type=str, default=None)

    def handle(self, *args, **options):
        nearest = find_nearest(Station, options["latitude"], options["longitude"], parser.parse(options["time"]))
        print(nearest)
