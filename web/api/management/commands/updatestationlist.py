# Update Station list from EXCEL or CSV file 

from glob import glob
import os
import sys
import io
import pandas as pd
import numpy as np
import openpyxl

from django.core.management.base import BaseCommand, CommandError
from api.models import Station, StationLocation 
from django.db import models, transaction
from datetime import date
from api.utils import parse_datetime_utc
from io import BytesIO

class Command(BaseCommand):
    help = 'Use --file to update Station List from EXCEL/CSV file. --stdin updates Station List from CSV files only.'

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, help='path to EXCEL/CSV file containing the Station List')
        parser.add_argument('--stdin', action='store_true', help='read CSV file from stdin', default=False)

    def handle(self, *args, **options):

        if options['file'] is None and not options['stdin']:
            self.stdout.write(self.help)
            return

        file = options.get('file')
        stdin = options['stdin']

        if file is not None:
            assert os.path.exists(file)
            file_extension = os.path.splitext(file)[1].lower()
            if file_extension == ".csv":
                df = pd.read_csv(file, header=0)
            elif file_extension in (".xlsx", ".xls"):
                df = pd.read_excel(file, header=0)
            else:
                raise ValueError("Unsupported file format. Only CSV, XLSX, and XLS files are supported.")
        else:
            try:
                df = pd.read_csv(sys.stdin)
            except Exception as e:
                raise CommandError(e)          
            
        # If the dates are "current", set to null      
        df['startDate'] = np.where(df['startDate'] == 'current', None, df['startDate'])
        df['endDate'] = np.where(df['endDate'] == 'current', None, df['endDate'])

        # Iterate through the rows of the DataFrame
        for index, row in df.iterrows():
           station_name = row['station']
           full_name = row['stationfullname']
           latitude = float(row['decimalLatitude'])
           longitude = float(row['decimalLongitude'])
           depth = float(row['depth_m'])
           comment = row['comment']

           start_date = parse_datetime_utc(row['startDate'])
           end_date = row['endDate']
           if end_date:
              end_date = parse_datetime_utc(end_date)
           
           # Create the station name if it doesn't already exist
           try:
               with transaction.atomic():
                   station, created = Station.objects.get_or_create(name=station_name)
                   station.full_name = full_name
                   station.set_location(latitude=latitude, longitude=longitude, start_time=start_date,
                                        end_time=end_date, depth=depth, comment=comment)
                   station.save()
           except Exception as e:
               # Handle exceptions, rollback will occur automatically
               print(f"An error occurred: {e}")


        all_stations = Station.objects.all()
        for station in all_stations:
            print("Station in db: ", station)
            locations = station.locations.all()
            print("Number Locations ", locations.count())