"""Modèle fourni : c'est ce que l'API expose."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Todo:
    """Une tâche.

    id          identifiant entier, attribué par le serveur (incrémental, à partir de 1)
    title       intitulé de la tâche (100 caractères au plus)
    done        vrai quand la tâche est terminée ; faux à la création
    created_at  date de création (UTC), au format ISO 8601 dans le JSON
    """

    id: int
    title: str
    done: bool
    created_at: datetime

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "done": self.done,
            "created_at": self.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
