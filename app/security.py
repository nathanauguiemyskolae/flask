"""Sécurité : émission et vérification des JWT (RS256). Fourni : vous apprenez à l'utiliser, pas à l'écrire.

Le serveur signe avec sa clé PRIVÉE ; la vérification, à chaque requête, n'utilise que la clé PUBLIQUE.
"""

import hmac
from datetime import datetime, timedelta, timezone
from functools import wraps
from pathlib import Path

import jwt
from flask import current_app, g, request

from .errors import ApiError

ROLE_ADMIN = "admin"
ROLE_USER = "user"

_DUMMY = "dummy-value-so-that-comparison-always-happens"


def _key(content_key: str, path_key: str) -> str:
    config = current_app.config
    return config[content_key] or Path(config[path_key]).read_text()


def authenticate_user(username: str, password: str) -> str | None:
    """Renvoie le rôle si les identifiants sont valides, sinon None.

    Simplification de TP : deux comptes dont les mots de passe viennent de l'environnement. Dans une vraie
    application, les comptes sont en base avec des mots de passe HACHÉS (bcrypt, argon2).
    """
    config = current_app.config
    accounts = {"admin": (config["ADMIN_PASSWORD"], ROLE_ADMIN), "user": (config["USER_PASSWORD"], ROLE_USER)}
    expected, role = accounts.get(username, ("", None))

    # Comparaison faite même pour un compte inconnu, et en temps constant : le temps de réponse ne trahit rien
    same = hmac.compare_digest((expected or _DUMMY).encode(), password.encode())
    return role if (expected and role and same) else None


def issue_token(username: str, role: str) -> tuple[str, datetime]:
    expires_at = (datetime.now(timezone.utc) + timedelta(seconds=current_app.config["JWT_TTL_SECONDS"])).replace(
        microsecond=0)
    claims = {
        "iss": current_app.config["JWT_ISSUER"],  # qui a émis le jeton
        "upn": username,  # identité
        "groups": [role],  # rôles
        "exp": expires_at,  # après cette date, le jeton est refusé
    }
    token = jwt.encode(claims, _key("JWT_PRIVATE_KEY", "JWT_PRIVATE_KEY_PATH"), algorithm="RS256")
    return token, expires_at


def _bearer() -> str:
    scheme, _, value = request.headers.get("Authorization", "").partition(" ")
    if scheme.lower() != "bearer" or not value.strip():
        raise ApiError(401, "Unauthenticated.")
    return value.strip()


def require_auth(*roles: str):
    """Décorateur : exige un jeton valide (401) et, si des rôles sont listés, l'un d'eux (403).

    @bp.get("/me")
    @require_auth()                 # tout jeton valide
    ...
    @bp.delete("/todos/<int:id>")
    @require_auth(ROLE_ADMIN)       # réservé au rôle admin
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                claims = jwt.decode(
                    _bearer(),
                    _key("JWT_PUBLIC_KEY", "JWT_PUBLIC_KEY_PATH"),
                    algorithms=["RS256"],  # jamais "none", jamais le choix du client
                    issuer=current_app.config["JWT_ISSUER"],
                    options={"require": ["exp", "iss"]},
                )
            except jwt.PyJWTError:
                raise ApiError(401, "Unauthenticated.")  # absent, falsifié, expiré, mauvais émetteur
            g.claims = claims
            if roles and not set(claims.get("groups", [])) & set(roles):
                raise ApiError(403, "This action is unauthorized.")
            return fn(*args, **kwargs)

        return wrapper

    return decorator
