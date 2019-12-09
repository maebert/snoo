from snoo.client import Client
from snoo import run
import pytest

def test_client():
    client = Client()
    assert client.config is not None

def test_cli():
    with pytest.raises(SystemExit):
        run()
