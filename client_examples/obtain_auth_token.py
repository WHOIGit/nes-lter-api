import os

import requests
import dotenv


def obtain_auth_token(url, username, password):
    data = {'username': username, 'password': password}
    response = requests.post(url, data=data)
    return response.json().get('token', None)


def main():
    url = os.getenv('NESLTER_API_BASE_URL', 'http://localhost:8000') + '/api-token-auth/'
    username = os.getenv('DJANGO_USER', 'my_django_username')
    password = os.getenv('DJANGO_PASSWORD', 'my_django_password')

    token = obtain_auth_token(url, username, password)

    print(token)


if __name__ == '__main__':
    dotenv.load_dotenv()
    main()
