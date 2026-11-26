from flask import Blueprint, g, jsonify

from ..security import require_auth

bp = Blueprint("me", __name__, url_prefix="/api/v1")


@bp.get("/me")
@require_auth()  # EXEMPLE d'une route PROTÉGÉE : sans jeton valide, 401 et ce code n'est pas exécuté
def me():
    """Renvoie l'identité lue DANS le jeton (g.claims, posé par le décorateur).

    Projet : c'est ce décorateur qu'on ajoutera aux routes de todos, puis @require_auth(ROLE_ADMIN)
    pour les actions réservées aux administrateurs.
    """
    return jsonify(data={"username": g.claims["upn"], "roles": g.claims["groups"]})
