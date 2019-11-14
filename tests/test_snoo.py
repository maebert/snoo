from snoo.client import Client


def test_client():
    client = Client()
    assert client.config is not None
