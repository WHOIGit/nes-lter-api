from django.core.management.base import BaseCommand, CommandError

from api.models import Station

class Command(BaseCommand):
    help = "Add station (name)"

    def add_arguments(self, parser):
        parser.add_argument("name", type=str)

    def handle(self, *args, **options):
        station = Station(name=options["name"])
        station.save()

        self.stdout.write(self.style.SUCCESS(f'Successfully created station {station.name}'))
