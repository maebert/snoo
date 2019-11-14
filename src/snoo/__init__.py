from .client import Client


def run():
    client = Client()
    print(client.status())


if __name__ == "__main__":
    run()
