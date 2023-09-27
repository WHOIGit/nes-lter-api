# workflows for processing, modifying, and producing data

from api.utils import regularize_column_names
from api.models import Station


def add_nearest_station(input_df, timestamp_column=None, latitude_column=None, longitude_column=None):

    df = regularize_column_names(input_df, {
        'latitude': ['lat', 'lt'] if latitude_column is None else [latitude_column],
        'longitude': ['lon', 'long', 'lng', 'lg'] if longitude_column is None else [longitude_column],
        'timestamp': ['time', 'datetime', 'date'] if timestamp_column is None else [timestamp_column]
    })

    for index, row in df.iterrows():
        # get the nearest station
        nearest_location = Station.nearest_location(row['latitude'], row['longitude'], row['timestamp'])
        # add the station's id to the row
        df.at[index, 'nearest_station'] = nearest_location.get_station().name
        df.at[index, 'distance_km'] = nearest_location.distance.m / 1000 # convert to km

    df.columns = list(input_df.columns) + ['nearest_station', 'distance_km']

    return df
