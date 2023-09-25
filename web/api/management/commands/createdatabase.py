# Create nes-lter-api Station Database from NES-LTER_station_list_compilation.xlsx
# Download NES-LTER_station_list_compilation.xlsx from https://docs.google.com/spreadsheets/d/19sg62kJmFu9lTnUCqg81b0nHiHcpp1CD/edit#gid=665860356
# to your local environment where this script is running.
# This script runs from your local repro folder.

from glob import glob
import os
import pandas as pd
import numpy as np

from django.core.management.base import BaseCommand, CommandError
from api.models import Station, StationLocation 
from django.db import models
from datetime import date
from api.utils import parse_datetime_utc

class Command(BaseCommand):
    help = 'Populate Station Database'

    def handle(self, *args, **options):

        # read first row as column headers from the Station List Compilation excel file
        df = pd.read_excel('../data/NES-LTER_station_list_compilation.xlsx', header=0)

        # If the dates are "current", set to null      
        df['startDate'] = np.where(df['startDate'] == 'current', None, df['startDate'])
        df['endDate'] = np.where(df['endDate'] == 'current', None, df['endDate'])

        # Iterate through the rows of the DataFrame
        for index, row in df.iterrows():
           station_name = row['station']
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
               station = Station.objects.get(name=station_name)
           except Station.DoesNotExist:
               print("Create Station ", station_name)
               station = Station(name=station_name)
               station.save()  
           station.set_location(latitude=latitude, longitude=longitude, start_time=start_date,
                                end_time=end_date, depth=depth, comment=comment)
           station.save()


        all_stations = Station.objects.all()
        for station in all_stations:
            print("Station in db ", station)
            locations = station.locations.all()
            print("Number Locations ", locations.count())