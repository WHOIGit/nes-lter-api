import os

import requests
import dotenv


def main():
    csv_file = 'client_examples/foo.csv'

    token = os.getenv('DJANGO_TOKEN', '')
    headers = { 'Authorization': f'Token {token}' }
    url = os.getenv('DJANGO_BASE_URL') + '/nearest_station_csv/'
    files = {'csv_file': open(csv_file, 'rb')}

    response = requests.post(url, files=files, headers=headers)

    print(response.text)


if __name__ == '__main__':
    dotenv.load_dotenv()
    main()
