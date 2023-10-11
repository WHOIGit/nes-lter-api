from neslter.api import Client

def main():
    client = Client()
    client.obtain_auth_token()

if __name__ == '__main__':
    main()
