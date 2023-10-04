# workflows for processing, modifying, and producing data
import pandas as pd 

from api.utils import regularize_column_names
from api.models import Station


def add_nearest_station(input_df, timestamp_column=None, latitude_column=None, longitude_column=None):

    # look for standard column names if none are provided
    df = regularize_column_names(input_df, {
        'latitude': ['lat', 'lt'] if latitude_column is None else [latitude_column],
        'longitude': ['lon', 'long', 'lng', 'lg'] if longitude_column is None else [longitude_column],
        'timestamp': ['time', 'datetime', 'date'] if timestamp_column is None else [timestamp_column]
    })

    if not {'latitude', 'longitude', 'timestamp'}.issubset(df.columns):
        raise ValueError('Missing one or more required columns: latitude, longitude, timestamp')
    
    # reject if either of these columns already exist
    if 'nearest_station' in df.columns or 'distance_km' in df.columns:
        raise ValueError('Cannot overwrite existing columns: nearest_station, distance_km')

    for index, row in df.iterrows():
        # check lat/lon for out of range values
        if row['latitude'] < -90 or row['latitude'] > 90:
            raise ValueError(f'Invalid latitude value: {row["latitude"]}')
        if row['longitude'] < -180 or row['longitude'] > 180:
            raise ValueError(f'Invalid longitude value: {row["longitude"]}')
        # get the nearest station
        nearest_location = Station.nearest_location(row['latitude'], row['longitude'], row['timestamp'])
        # add the station's id to the row
        df.at[index, 'nearest_station'] = nearest_location.get_station().name
        df.at[index, 'distance_km'] = nearest_location.distance.m / 1000 # convert to km

    # use original column names for existing columns
    df.columns = list(input_df.columns) + ['nearest_station', 'distance_km']

    return df


def station_list(timestamp=None):
    # get the current location of each Station
    stations = Station.objects.all()
    station_locations = [station.get_location(timestamp) for station in stations]
    # format as a DataFrame with station name, lat, lon, depth, and comment
    df = pd.DataFrame.from_records([{
        'station': station.name,
        'latitude': location.geolocation.y,
        'longitude': location.geolocation.x,
        'depth_m': location.depth,
        'comment': location.comment
    } for station, location in zip(stations, station_locations) if location is not None])
    if df.empty:
        return df
    # sort by station name
    df.sort_values('station', inplace=True)
    # reset the index
    df.reset_index(drop=True, inplace=True)
    # return the DataFrame
    return df
