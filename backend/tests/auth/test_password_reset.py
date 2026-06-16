from .conftest import login, register


def test_forgot_password_existing_email_sends_mail(client, outbox):
    register(client, email="fp@example.com")
    resp = client.post("/api/v1/auth/forgot-password", json={"email": "fp@example.com"})
    assert resp.status_code == 200
    assert len(outbox) == 1
    assert outbox[0]["purpose"] == "reset_password"


def test_forgot_password_unknown_email_silent(client, outbox):
    # Must not leak account existence.
    resp = client.post("/api/v1/auth/forgot-password", json={"email": "nope@example.com"})
    assert resp.status_code == 200
    assert outbox == []


def test_reset_password_success(client, outbox):
    register(client, email="rp@example.com")
    client.post("/api/v1/auth/forgot-password", json={"email": "rp@example.com"})
    token = outbox[0]["token"]
    resp = client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": "Newstrong1pass"},
    )
    assert resp.status_code == 200
    assert login(client, "rp@example.com", "Strongpass1").status_code == 401
    assert login(client, "rp@example.com", "Newstrong1pass").status_code == 200


def test_reset_password_invalid_token(client):
    resp = client.post(
        "/api/v1/auth/reset-password",
        json={"token": "bad", "new_password": "Newstrong1pass"},
    )
    assert resp.status_code == 400


def test_reset_password_weak(client, outbox):
    register(client, email="rpw@example.com")
    client.post("/api/v1/auth/forgot-password", json={"email": "rpw@example.com"})
    token = outbox[0]["token"]
    resp = client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": "short"},
    )
    assert resp.status_code == 422