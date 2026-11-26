"""Stockage des tâches EN MÉMOIRE : aucune base de données.

Conséquences à comprendre (voir le cours, section 3.3) :
 - tout est perdu quand l'application s'arrête ;
 - une seule instance de l'API peut tourner (deux instances auraient chacune leurs données). C'est pour cela que
   gunicorn est lancé avec UN SEUL processus : plusieurs processus auraient chacun leur mémoire ;
 - plusieurs requêtes arrivent EN MÊME TEMPS (gunicorn utilise plusieurs threads) : les modifications de
   l'état partagé doivent être protégées.

TP 3, étape 3 : compléter la classe. Tant qu'elle n'est pas écrite, l'API répond 500 sur les routes todos.
"""
from dataclasses import replace
from datetime import datetime, timezone
import threading 


from .models import Todo


class TodoStore:
    def __init__(self) -> None:
        self._todos: dict[int, Todo] = {}   # tâches par identifiant
        self._next_id = 1                    # prochain identifiant à attribuer
        self._lock = threading.Lock()        # protège les deux lignes ci-dessus

    def create(self, title: str) -> Todo:
        with self._lock:   # une seule requête à la fois entre ici...
            todo = Todo(self._next_id, title, False, datetime.now(timezone.utc).replace(microsecond=0))
            self._todos[todo.id] = todo
            self._next_id += 1
        return todo        # ... et ici

    def find_all(self, done: bool | None = None) -> list[Todo]:
        with self._lock:
            todos = self._todos.values()
            if done is not None:
                todos = [t for t in todos if t.done is done]
            return sorted(todos, key=lambda todo: todo.id)

    def find_by_id(self, todo_id: int) -> Todo | None:
        with self._lock:
            return self._todos.get(todo_id)

    def update(self, todo_id: int, title: str | None = None, done: bool | None = None) -> Todo | None:
        with self._lock:  # lecture, modification et écriture : sous le verrou
            old = self._todos.get(todo_id)
            if old is None:
                return None
            new = replace(
                old,
                title=title if title is not None else old.title,
                done=done if done is not None else old.done,
            )
            self._todos[todo_id] = new
            return new

    def delete(self, todo_id: int) -> bool:
        with self._lock:
            return self._todos.pop(todo_id, None) is not None

# Instance unique, partagée par toute l'application (équivalent d'un @ApplicationScoped)
store = TodoStore()
