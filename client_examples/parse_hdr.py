import os

import requests
import dotenv


def main():
    hdr_file = 'client_examples/EN627_026_u.hdr'

    token = os.getenv('DJANGO_TOKEN', '')
    headers = { 'Authorization': f'Token {token}' }
    url = os.getenv('DJANGO_BASE_URL') + '/parse-ctd-hdr/'
    files = {'hdr_file': open(hdr_file, 'rb')}

    response = requests.post(url, files=files, headers=headers)

    print(response.text)


if __name__ == '__main__':
    dotenv.load_dotenv()
    main()
