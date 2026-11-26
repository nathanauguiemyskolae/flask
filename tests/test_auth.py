"""Tests du socle fourni : login, route protégée et route publique. Verts dès le départ."""

from tests.conftest import ADMIN_PASSWORD, ADMIN_USERNAME


def test_login_returns_bearer_token(client):
    response = client.post("/api/v1/auth/login", json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD})

    assert response.status_code == 200
    body = response.get_json()
    assert body["token_type"] == "Bearer"
    assert body["token"] and body["expires_at"]


def test_same_message_for_unknown_user_and_wrong_password(client):
    wrong_password = client.post("/api/v1/auth/login", json={"username": ADMIN_USERNAME, "password": "faux"})
    unknown_user = client.post("/api/v1/auth/login", json={"username": "inconnu", "password": "faux"})

    assert wrong_password.status_code == unknown_user.status_code == 401
    assert wrong_password.get_json() == unknown_user.get_json() == {"message": "Invalid credentials."}


def test_login_body_is_validated(client):
    response = client.post("/api/v1/auth/login", json={"username": ""})

    assert response.status_code == 422
    assert {"username", "password"} <= set(response.get_json()["errors"])


def test_protected_route_requires_token(client):
    response = client.get("/api/v1/me")

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert response.get_json() == {"message": "Unauthenticated."}


def test_protected_route_rejects_invalid_token(client):
    response = client.get("/api/v1/me", headers={"Authorization": "Bearer pas-un-jwt"})

    assert response.status_code == 401


def test_protected_route_returns_identity_read_from_token(client, admin_token):
    response = client.get("/api/v1/me", headers={"Authorization": f"Bearer {admin_token}"})

    assert response.status_code == 200
    assert response.get_json()["data"] == {"username": "admin", "roles": ["admin"]}
