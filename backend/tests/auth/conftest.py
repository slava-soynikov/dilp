"""Helpers shared by auth tests."""
import pytest


def register(client, email: str = "user@example.com", password: str = "Strongpass1", role: str = "parent"):
    return client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "role": role},
    )


def login(client, email: str, password: str):
    return client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )


@pytest.fixture
def verified_parent(client, outbox):
    """Registered parent — active immediately, no email-verification step."""
    email, password = "user@example.com", "Strongpass1"
    register(client, email=email, password=password)
    return {"email": email, "password": password}