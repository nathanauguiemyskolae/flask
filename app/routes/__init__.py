"""Enregistrement des blueprints. Une revue de sécurité commence par la liste des routes :
    flask --app app routes
"""

from flask import Flask


def register_blueprints(app: Flask) -> None:
    from .auth import bp as auth_bp
    from .docs import bp as docs_bp
    from .health import bp as health_bp
    from .me import bp as me_bp
    from .todos import bp as todos_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(me_bp)
    app.register_blueprint(todos_bp)
    app.register_blueprint(docs_bp)
