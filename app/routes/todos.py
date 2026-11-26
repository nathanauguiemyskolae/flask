"""Ressource "todos".

TP 3, étape 4 : écrire les trois routes (voir le cours, section 3.3).
  POST /api/v1/todos        créer une tâche      (201 + Location, 422 si le titre est invalide)
  GET  /api/v1/todos        lister les tâches    (200)
  GET  /api/v1/todos/<id>   lire une tâche       (200, 404 si inconnue)

Les erreurs (404, 422...) sont mises en forme par app/errors.py : il suffit de lever une ApiError
ou de laisser la validation (marshmallow) échouer.
"""

from flask import Blueprint, jsonify, request, url_for
from marshmallow import ValidationError

from ..errors import ApiError
from ..schemas import TodoInputSchema, TodoUpdateSchema
from ..security import ROLE_ADMIN, require_auth
from ..store import store

bp = Blueprint("todos", __name__, url_prefix="/api/v1")


@bp.post("/todos")
@require_auth()
def create_todo():
    data = TodoInputSchema().load(request.get_json())   # 422 si invalide (ValidationError, voir errors.py)
    todo = store.create(data["title"])

    # L'adresse de la ressource créée, renvoyée dans l'en-tête Location
    location = url_for("todos.get_todo", todo_id=todo.id)
    return jsonify(data=todo.to_dict()), 201, {"Location": location}


@bp.get("/todos")
@require_auth()
def list_todos():
    done_param = request.args.get("done")
    if done_param is None:
        done_filter = None
    elif done_param == "true":
        done_filter = True
    elif done_param == "false":
        done_filter = False
    else:
        raise ValidationError({"done": ["Must be 'true' or 'false'."]})

    return jsonify(data=[todo.to_dict() for todo in store.find_all(done=done_filter)])


@bp.get("/todos/<int:todo_id>")
@require_auth()
def get_todo(todo_id: int):
    todo = store.find_by_id(todo_id)
    if todo is None:
        raise ApiError(404, "Todo not found.")   # transformé en 404 JSON par errors.py
    return jsonify(data=todo.to_dict())


@bp.patch("/todos/<int:todo_id>")
@require_auth()
def update_todo(todo_id: int):
    json_data = request.get_json(silent=True)
    if json_data is None:
        json_data = {}
    data = TodoUpdateSchema().load(json_data)
    todo = store.update(todo_id, title=data.get("title"), done=data.get("done"))
    if todo is None:
        raise ApiError(404, "Todo not found.")
    return jsonify(data=todo.to_dict())


@bp.delete("/todos/<int:todo_id>")
@require_auth(ROLE_ADMIN)
def delete_todo(todo_id: int):
    if not store.delete(todo_id):
        raise ApiError(404, "Todo not found.")
    return "", 204
