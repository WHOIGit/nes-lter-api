import os
from io import StringIO

import requests
import dotenv
import pandas as pd

from client import Client


def with_client(csv_file):
    client = Client()

    df = client.add_nearest_stations(csv_file, timestamp_column='sample_time')
    print(df.head())

    df = client.station_list(timestamp='2019-01-01T00:00:00Z')
    print(df.head())


def main():
    csv_file = 'client_examples/foo.csv'

    with_client(csv_file)


if __name__ == '__main__':
    dotenv.load_dotenv()
    main()
