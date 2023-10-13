import dotenv
import requests

from .utils import add_auth_headers, construct_api_url, parse_csv_response, post_csv, parse_ctd, obtain_auth_token

class Client(object):

    def __init__(self, loadenv=True):
        if loadenv:
            dotenv.load_dotenv()

    def obtain_auth_token(self):
        obtain_auth_token()
    
    def parse_hdr(self, hdr_file):
        return parse_ctd(hdr_file, 'hdr')
    
    def parse_btl(self, btl_file):
        return parse_ctd(btl_file, 'btl')
    
    def parse_asc(self, asc_file):
        return parse_ctd(asc_file, 'asc')
    
    def create_station(self, station_name, full_name):
        suffix = '/stations/'
        url = construct_api_url(suffix)
        data = {'name': station_name, 'full_name': full_name}
        response = requests.post(url, data=data, headers=add_auth_headers())
        return response

    def delete_station(self, station_name):
        suffix = f'/stations/{station_name}'
        url = construct_api_url(suffix)
        response = requests.delete(url, headers=add_auth_headers())
        return response

    def add_station_location(self, station_name, latitude, longitude,
                             start_time, end_time=None, depth=None):
        suffix = '/add-station-location/'
        url = construct_api_url(suffix)
        data = {'name': station_name, 'latitude': latitude,
                'longitude': longitude, 'depth': depth,
                'start_time': start_time, 'end_time': end_time}
        response = requests.post(url, data=data, headers=add_auth_headers())
        return response

    def station_list(self, timestamp=None):
        suffix = '/station-list'
        url = construct_api_url(suffix)
        params = {'timestamp': timestamp} if timestamp else {}
        response = requests.get(url, params=params)
        return parse_csv_response(response)

    def nearest_station(self, latitude, longitude, timestamp=None):
        suffix = '/nearest-station'
        url = construct_api_url(suffix)
        params = {'latitude': latitude, 'longitude': longitude}
        if timestamp is not None:
            params['timestamp'] = timestamp
        response = requests.get(url, params=params).json()[0]
        return {
            'name': response['station']['name'],
            'distance_km': response['distance'],
            'latitude': response['geolocation']['latitude'],
            'longitude': response['geolocation']['longitude'],
            'depth': response['depth'],
            'comment': response['comment'],
        }

    def add_nearest_stations(self, csv_file, timestamp_column=None, latitude_column=None, longitude_column=None):
        # TODO accept dataframe as input in addition to CSV file
        suffix = '/add-nearest-stations/'
        url = construct_api_url(suffix)
        params = {}
        if timestamp_column is not None:
            params['timestamp_column'] = timestamp_column
        if latitude_column is not None:
            params['latitude_column'] = latitude_column
        if longitude_column is not None:
            params['longitude_column'] = longitude_column
        response = post_csv(url, csv_file, csv_filename='csv_file', params=params)
        return parse_csv_response(response)
