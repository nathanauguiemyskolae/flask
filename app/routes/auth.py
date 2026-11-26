from flask import Blueprint, jsonify, request

from ..errors import ApiError
from ..schemas import LoginSchema
from ..security import authenticate_user, issue_token

bp = Blueprint("auth", __name__, url_prefix="/api/v1")


@bp.post("/auth/login")  # Route PUBLIQUE : on ne peut pas exiger un jeton pour en obtenir un
def login():
    """Le client envoie ses identifiants, le serveur répond par un JWT signé."""
    data = LoginSchema().load(request.get_json())  # 422 si invalide
    role = authenticate_user(data["username"], data["password"])
    if role is None:
        # Même message que le compte soit inconnu ou le mot de passe faux : pas d'énumération des comptes
        raise ApiError(401, "Invalid credentials.")

    token, expires_at = issue_token(data["username"], role)
    return jsonify(token=token, token_type="Bearer", expires_at=expires_at.strftime("%Y-%m-%dT%H:%M:%SZ"))
