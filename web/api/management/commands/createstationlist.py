# Update Station list from EXCEL or CSV file 

import os
import sys
import pandas as pd
import numpy as np

from django.core.management.base import BaseCommand, CommandError
from api.models import Station 
from django.db import transaction
from api.utils import parse_datetime_utc


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
        df.dropna(subset=['startDate'], inplace=True)
        df['comment'] = df['comment'].fillna('')

        with transaction.atomic():
            # empty database
            Station.objects.all().delete()

            for station_name, sdf in df.groupby('station'):
                station = Station.objects.create(name=station_name)
    
                for row in sdf.itertuples():
                    latitude = float(row.decimalLatitude)
                    longitude = float(row.decimalLongitude)
                    depth = float(row.depth_m) if not np.isnan(row.depth_m) else None

                    # check if lat/lon are valid
                    if latitude < -90 or latitude > 90 or longitude < -180 or longitude > 180:
                        raise ValueError(f"Invalid latitude/longitude for station {station_name}: {latitude}, {longitude}")
                    
                    # check if depth is positive
                    if depth is not None and depth < 0:
                        raise ValueError(f"Negative depth for station {station_name}: {depth}")
                    
                    comment = row.comment if row.comment else None

                    start_date = parse_datetime_utc(row.startDate)
                    end_date = parse_datetime_utc(row.endDate) if row.endDate else None

                    station.set_location(latitude=latitude, longitude=longitude, start_time=start_date,
                                         end_time=end_date, depth=depth, comment=comment)
