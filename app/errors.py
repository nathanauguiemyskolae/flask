"""GESTION CENTRALISÉE DES ERREURS (fournie : voir le cours, section 3.4).

Principe : une route ne fabrique jamais une réponse d'erreur à la main. Elle lève une exception, et c'est
UN SEUL endroit, ici, qui la transforme en réponse JSON uniforme { "message": "..." }.
Le client écrit ainsi un seul gestionnaire d'erreurs, et aucune trace Python ne fuit jamais vers lui.

Exception levée                      -> Réponse
ApiError(status, message)            -> status choisi par le code (404, 409...)
marshmallow.ValidationError          -> 422 + détail par champ
JSON mal formé, méthode inconnue...  -> 400, 405, 415... (HTTPException)
absence ou invalidité du jeton       -> 401 + WWW-Authenticate: Bearer (ApiError)
rôle insuffisant                     -> 403 (ApiError)
route ou identifiant inconnu         -> 404
toute autre exception (un bug)       -> 500 SANS détail ; la trace va dans les journaux
"""

from flask import Flask, jsonify
from marshmallow import ValidationError
from werkzeug.exceptions import HTTPException


class ApiError(Exception):
    """Erreur volontaire du code. Usage : raise ApiError(404, "Todo not found.")"""

    def __init__(self, status: int, message: str, headers: dict | None = None):
        super().__init__(message)
        self.status = status
        self.message = message
        self.headers = headers or {}


# Messages génériques pour les erreurs HTTP produites par Flask lui-même
_HTTP_MESSAGES = {
    404: "Resource not found.",
    405: "Method not allowed.",
    413: "Payload too large.",
}


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(ApiError)
    def api_error(err: ApiError):
        headers = dict(err.headers)
        if err.status == 401:
            headers.setdefault("WWW-Authenticate", "Bearer")  # exigé par la RFC 6750
        return jsonify(message=err.message), err.status, headers

    @app.errorhandler(ValidationError)
    def validation_error(err: ValidationError):
        return jsonify(message="The given data was invalid.", errors=err.messages), 422

    @app.errorhandler(HTTPException)
    def http_error(err: HTTPException):
        return jsonify(message=_HTTP_MESSAGES.get(err.code, err.description)), err.code

    @app.errorhandler(Exception)  # tout le reste : 500 sans aucun détail pour le client
    def unexpected(err: Exception):
        app.logger.exception("Unhandled error")  # la trace va dans les journaux
        return jsonify(message="Server Error."), 500
