from flask import Blueprint, jsonify

bp = Blueprint("health", __name__, url_prefix="/api/v1")


@bp.get("/health")  # EXEMPLE d'une route PUBLIQUE : aucun décorateur @require_auth, aucun jeton demandé
def health():
    """C'est la route qu'une sonde de supervision ou un orchestrateur appelle pour savoir si le service répond.

    Elle est volontairement pauvre en informations : elle dit si le service fonctionne, rien de plus.
    """
    return jsonify(status="ok")
