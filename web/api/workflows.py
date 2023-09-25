# workflows for processing, modifying, and producing data

from api.utils import regularize_column_names
from api.models import Station


def add_nearest_station(df):

    df = regularize_column_names(df, {
        'latitude': ['lat', 'lt'],
        'longitude': ['lon', 'long', 'lng', 'lg'],
        'timestamp': ['time', 'datetime', 'date']
    })

    for index, row in df.iterrows():
        # get the nearest station
        nearest_location = Station.nearest_location(row['latitude'], row['longitude'], row['timestamp'])
        # add the station's id to the row
        df.at[index, 'station'] = nearest_location.get_station().name
        df.at[index, 'distance_km'] = nearest_location.distance.m / 1000 # convert to km

    return df
