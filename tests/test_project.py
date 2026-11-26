"""Tests complémentaires du Projet :
- Concurrence sur TodoStore (test unitaire sans HTTP : 100 threads simultanés)
- PATCH /todos/<id> (nominal 200, 404, 422 corps vide, 422 titre invalide)
- DELETE /todos/<id> (admin 204, relire 404, inconnu 404)
- Filtre ?done= (true, false, 422 si invalide)
- Sécurité (401 sans jeton, 403 si rôle user sur DELETE)
"""

import concurrent.futures

from app.store import TodoStore


# 1. Test unitaire du stockage sans HTTP (concurrence)
def test_concurrent_store_creation():
    store = TodoStore()
    count = 100

    def worker(i):
        return store.create(f"Task {i}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(worker, i) for i in range(count)]
        todos = [f.result() for f in concurrent.futures.as_completed(futures)]

    assert len(todos) == count
    # Vérification : 100 identifiants uniques
    ids = {t.id for t in todos}
    assert len(ids) == count
    assert ids == set(range(1, count + 1))
    assert len(store.find_all()) == count


# 2. Tests de sécurité (401 et 403)
def test_unauthenticated_access_is_401(client):
    """Sans jeton Bearer, l'API renvoie 401."""
    assert client.get("/api/v1/todos").status_code == 401
    assert client.post("/api/v1/todos", json={"title": "Test"}).status_code == 401
    assert client.patch("/api/v1/todos/1", json={"done": True}).status_code == 401
    assert client.delete("/api/v1/todos/1").status_code == 401


def test_user_cannot_delete_todo_is_403(client, user_headers, admin_headers):
    """Le rôle 'user' ne peut pas supprimer (réservé à 'admin' -> 403)."""
    # Création par l'admin
    created = client.post("/api/v1/todos", json={"title": "À ne pas supprimer par user"}, headers=admin_headers)
    todo_id = created.get_json()["data"]["id"]

    # Tentative de suppression par l'utilisateur simple -> 403
    response = client.delete(f"/api/v1/todos/{todo_id}", headers=user_headers)
    assert response.status_code == 403
    assert "message" in response.get_json()


# 3. Tests PATCH
def test_patch_nominal_updates_fields(client, admin_headers):
    created = client.post("/api/v1/todos", json={"title": "Tâche à modifier"}, headers=admin_headers)
    todo_id = created.get_json()["data"]["id"]

    # Modification de 'done' uniquement
    res1 = client.patch(f"/api/v1/todos/{todo_id}", json={"done": True}, headers=admin_headers)
    assert res1.status_code == 200
    assert res1.get_json()["data"]["done"] is True
    assert res1.get_json()["data"]["title"] == "Tâche à modifier"

    # Modification de 'title' uniquement
    res2 = client.patch(f"/api/v1/todos/{todo_id}", json={"title": "Nouveau titre"}, headers=admin_headers)
    assert res2.status_code == 200
    assert res2.get_json()["data"]["title"] == "Nouveau titre"
    assert res2.get_json()["data"]["done"] is True

    # Modification des deux champs simultanément
    res3 = client.patch(
        f"/api/v1/todos/{todo_id}", json={"title": "Titre final", "done": False}, headers=admin_headers
    )
    assert res3.status_code == 200
    assert res3.get_json()["data"]["title"] == "Titre final"
    assert res3.get_json()["data"]["done"] is False


def test_patch_empty_body_is_422(client, admin_headers):
    created = client.post("/api/v1/todos", json={"title": "Test vide"}, headers=admin_headers)
    todo_id = created.get_json()["data"]["id"]

    response = client.patch(f"/api/v1/todos/{todo_id}", json={}, headers=admin_headers)
    assert response.status_code == 422


def test_patch_invalid_title_is_422(client, admin_headers):
    created = client.post("/api/v1/todos", json={"title": "Test titre"}, headers=admin_headers)
    todo_id = created.get_json()["data"]["id"]

    # Titre vide
    assert client.patch(f"/api/v1/todos/{todo_id}", json={"title": ""}, headers=admin_headers).status_code == 422
    assert client.patch(f"/api/v1/todos/{todo_id}", json={"title": "   "}, headers=admin_headers).status_code == 422

    # Titre supérieur à 100 caractères
    assert client.patch(f"/api/v1/todos/{todo_id}", json={"title": "a" * 101}, headers=admin_headers).status_code == 422


def test_patch_unknown_todo_is_404(client, admin_headers):
    response = client.patch("/api/v1/todos/999999", json={"done": True}, headers=admin_headers)
    assert response.status_code == 404


# 4. Tests DELETE
def test_delete_nominal_by_admin_is_204_and_then_404(client, admin_headers):
    created = client.post("/api/v1/todos", json={"title": "Tâche à détruire"}, headers=admin_headers)
    todo_id = created.get_json()["data"]["id"]

    # Suppression par admin : 204 sans corps
    response = client.delete(f"/api/v1/todos/{todo_id}", headers=admin_headers)
    assert response.status_code == 204
    assert response.data == b""

    # Deuxième lecture ou suppression : 404
    assert client.get(f"/api/v1/todos/{todo_id}", headers=admin_headers).status_code == 404
    assert client.delete(f"/api/v1/todos/{todo_id}", headers=admin_headers).status_code == 404


def test_delete_unknown_is_404(client, admin_headers):
    assert client.delete("/api/v1/todos/888888", headers=admin_headers).status_code == 404


# 5. Tests filtre ?done=
def test_filter_by_done_status(client, admin_headers):
    # Créer une tâche non terminée et une terminée
    t1 = client.post("/api/v1/todos", json={"title": "Filtre Todo Incomplete"}, headers=admin_headers).get_json()[
        "data"
    ]["id"]
    t2 = client.post("/api/v1/todos", json={"title": "Filtre Todo Done"}, headers=admin_headers).get_json()["data"][
        "id"
    ]
    client.patch(f"/api/v1/todos/{t2}", json={"done": True}, headers=admin_headers)

    # Filtrer done=false
    res_false = client.get("/api/v1/todos?done=false", headers=admin_headers)
    assert res_false.status_code == 200
    ids_false = [t["id"] for t in res_false.get_json()["data"]]
    assert t1 in ids_false
    assert t2 not in ids_false

    # Filtrer done=true
    res_true = client.get("/api/v1/todos?done=true", headers=admin_headers)
    assert res_true.status_code == 200
    ids_true = [t["id"] for t in res_true.get_json()["data"]]
    assert t2 in ids_true
    assert t1 not in ids_true


def test_filter_with_invalid_value_is_422(client, admin_headers):
    response = client.get("/api/v1/todos?done=maybe", headers=admin_headers)
    assert response.status_code == 422
    assert "done" in response.get_json()["errors"]
