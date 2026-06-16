import pytest

from tests.auth.conftest import login, register


def auth_header(client, email="user@example.com", password="Strongpass1"):
    register(client, email=email, password=password)
    token = login(client, email, password).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, email


@pytest.fixture
def parent_auth(client, outbox):
    headers, email = auth_header(client)
    return {"headers": headers, "email": email}