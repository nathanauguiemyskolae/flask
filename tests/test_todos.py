"""TP 3 : les trois routes de l'API Todo. Ces tests décrivent le contrat (cours, section 3.2).
Ils sont ROUGES au départ. Ne les modifiez pas : faites-les passer au vert.

    docker compose run --rm tests pytest tests/test_todos.py

L'application est partagée par tous les tests : aucun ne suppose que la liste est vide.
"""

import pytest


@pytest.fixture(autouse=True)
def _authenticate(client, admin_token):
    client.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {admin_token}"


def create(client, title):
    return client.post("/api/v1/todos", json={"title": title})


# ---------- POST /todos ----------

def test_create_returns_201_with_location_and_the_new_todo(client):
    response = create(client, "Sauvegarder la base")

    assert response.status_code == 201
    todo = response.get_json()["data"]
    assert isinstance(todo["id"], int) and todo["id"] > 0
    assert todo["title"] == "Sauvegarder la base"
    assert todo["done"] is False
    assert todo["created_at"]
    assert response.headers["Location"].endswith(f"/api/v1/todos/{todo['id']}")


def test_identifiers_increase(client):
    first = create(client, "Première").get_json()["data"]["id"]
    second = create(client, "Seconde").get_json()["data"]["id"]

    assert second > first


def test_title_is_required(client):
    response = client.post("/api/v1/todos", json={})

    assert response.status_code == 422
    body = response.get_json()
    assert "message" in body
    assert "title" in body["errors"]


def test_blank_title_is_refused(client):
    for blank in ("", "   "):
        response = create(client, blank)
        assert response.status_code == 422, repr(blank)
        assert "title" in response.get_json()["errors"]


def test_title_longer_than_100_characters_is_refused(client):
    assert create(client, "x" * 100).status_code == 201

    response = create(client, "x" * 101)
    assert response.status_code == 422
    assert "title" in response.get_json()["errors"]


def test_client_cannot_choose_the_state_of_a_new_todo(client):
    """Un champ non prévu par le contrat est ignoré : une tâche naît toujours non terminée."""
    response = client.post("/api/v1/todos", json={"title": "Tentative", "done": True, "id": 999999})

    assert response.status_code == 201
    todo = response.get_json()["data"]
    assert todo["done"] is False
    assert todo["id"] != 999999


# ---------- GET /todos ----------

def test_list_contains_the_created_todo(client):
    todo_id = create(client, "Vérifier les sauvegardes").get_json()["data"]["id"]

    response = client.get("/api/v1/todos")

    assert response.status_code == 200
    todos = response.get_json()["data"]
    assert todo_id in [t["id"] for t in todos]
    assert "Vérifier les sauvegardes" in [t["title"] for t in todos]


def test_list_is_ordered_by_identifier(client):
    create(client, "A")
    create(client, "B")

    ids = [t["id"] for t in client.get("/api/v1/todos").get_json()["data"]]

    assert ids == sorted(ids)


# ---------- GET /todos/<id> ----------

def test_show_returns_one_todo(client):
    todo_id = create(client, "Mettre à jour le serveur").get_json()["data"]["id"]

    response = client.get(f"/api/v1/todos/{todo_id}")

    assert response.status_code == 200
    todo = response.get_json()["data"]
    assert todo["id"] == todo_id
    assert todo["title"] == "Mettre à jour le serveur"
    assert todo["done"] is False


def test_unknown_identifier_is_404_with_a_json_message(client):
    response = client.get("/api/v1/todos/999999999")

    assert response.status_code == 404
    assert "message" in response.get_json()


def test_non_numeric_identifier_is_404(client):
    assert client.get("/api/v1/todos/abc").status_code == 404
