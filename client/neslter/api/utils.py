import os
from io import StringIO
from getpass import getpass

import requests
import pandas as pd


def add_auth_headers(headers={}):
    token = os.getenv('NESLTER_API_TOKEN')
    if token is None:
        raise ValueError('NESLTER_API_TOKEN environment variable not set')
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
    base_url = os.getenv('NESLTER_API_BASE_URL')
    if base_url is None:
        raise ValueError('NESLTER_API_BASE_URL environment variable not set')
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
    os.environ['NESLTER_API_TOKEN'] = token
    print('Add this to your .env file. Do not commit it to git.')
    print(f'NESLTER_API_TOKEN={token}')
