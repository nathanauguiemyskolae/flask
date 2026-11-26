"""Test du socle fourni : la route publique répond sans jeton. Vert dès le départ."""


def test_health_is_public(client):
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}
