"""API Todo : fabrique d'application Flask."""

from flask import Flask

from .config import Config


def create_app(config_object: type | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_object or Config)
    app.json.sort_keys = False  # garder l'ordre des champs tel qu'il est écrit

    from .errors import register_error_handlers
    from .routes import register_blueprints

    register_error_handlers(app)
    register_blueprints(app)
    return app
