from django.core.management.base import BaseCommand, CommandError

from dateutil import parser

from api.models import Station

class Command(BaseCommand):
    help = "Set station location (name)"

    def add_arguments(self, parser):
        parser.add_argument("name", type=str)
        parser.add_argument("latitude", type=float)
        parser.add_argument("longitude", type=float)
        parser.add_argument("depth", type=float)
        parser.add_argument("start_time", type=str)
        parser.add_argument("end_time", type=str)
        parser.add_argument("comments", type=str, default=None)

    def handle(self, *args, **options):
        station = Station.objects.get(name=options["name"])
        if station is None:
            raise CommandError(f"Station {options['name']} not found")
        station.set_coordinates(
            options["latitude"],
            options["longitude"],
            options["depth"],
            parser.parse(options["start_time"]),
            parser.parse(options["end_time"]),
            options["comments"]
        )
