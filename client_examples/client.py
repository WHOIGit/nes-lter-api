import os
from io import StringIO
from getpass import getpass

import requests
import pandas as pd


def add_auth_headers(headers={}):
    token = os.getenv('DJANGO_TOKEN')
    if token is None:
        raise ValueError('DJANGO_TOKEN environment variable not set')
    headers['Authorization'] = f'Token {token}'
    return headers


def post_csv(url, csv_file, csv_filename=None, headers={}, params={}):
    headers = add_auth_headers(headers)
    files = {csv_filename: open(csv_file, 'rb')}
    response = requests.post(url, files=files, headers=headers, params=params)
    return response


def parse_csv_response(response):
    df = pd.read_csv(StringIO(response.text))
    return df


def construct_api_url(suffix):
    base_url = os.getenv('DJANGO_BASE_URL')
    if base_url is None:
        raise ValueError('DJANGO_BASE_URL environment variable not set')
    url = base_url + suffix
    return url


def parse_ctd(ctd_file, file_type):
    suffix = f'/parse-ctd-{file_type}/'
    url = construct_api_url(suffix)
    response = post_csv(url, ctd_file, csv_filename=f'{file_type}_file')
    return parse_csv_response(response)


def obtain_auth_token():
    url = construct_api_url('/api-token-auth/')
    # read username and password from user
    username = input('Username: ')
    password = getpass('Password: ')
    data = {'username': username, 'password': password}
    response = requests.post(url, data=data)
    if response.status_code != 200:
        raise ValueError('Invalid username or password')
    token = response.json().get('token')
    print('Add this to your .env file')
    print(f'DJANGO_TOKEN={token}')


class Client(object):

    def __init__(self):
        pass
    
    def parse_hdr(self, hdr_file):
        return parse_ctd(hdr_file, 'hdr')
    
    def parse_btl(self, btl_file):
        return parse_ctd(btl_file, 'btl')
    
    def parse_asc(self, asc_file):
        return parse_ctd(asc_file, 'asc')
    
    def station_list(self, timestamp):
        suffix = '/station-list'
        url = construct_api_url(suffix)
        params = {'timestamp': timestamp}
        response = requests.get(url, params=params)
        return parse_csv_response(response)

    def add_nearest_stations(self, csv_file, timestamp_column=None, latitude_column=None, longitude_column=None):
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
