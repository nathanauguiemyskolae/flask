"""Schémas marshmallow : validation des entrées (load).

Règle : une entrée n'est jamais utilisée sans passer par un schéma. Un schéma décrit EXACTEMENT ce que le client
a le droit d'envoyer ; avec unknown = EXCLUDE, tout autre champ est ignoré (défense contre le mass assignment).
"""

from marshmallow import EXCLUDE, Schema, ValidationError, fields, validate, validates_schema



class LoginSchema(Schema):
    """Exemple fourni de schéma d'entrée."""

    class Meta:
        unknown = EXCLUDE

    username = fields.String(required=True, validate=validate.Length(min=1, max=50))
    password = fields.String(required=True, validate=validate.Length(min=1, max=255))


def _not_blank(value: str) -> None:
    if not value.strip():
        raise ValidationError("Title must not be blank.")


class TodoInputSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    title = fields.String(required=True, validate=[validate.Length(max=100), _not_blank])


class TodoUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    title = fields.String(required=False, validate=[validate.Length(max=100), _not_blank])
    done = fields.Boolean(required=False)

    @validates_schema
    def validate_at_least_one(self, data, **kwargs):
        if "title" not in data and "done" not in data:
            raise ValidationError("At least one of 'title' or 'done' must be provided.")
