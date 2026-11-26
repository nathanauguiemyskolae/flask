"""Documentation : le contrat docs/openapi.yaml, servi tel quel et affiché par Swagger UI.

Approche « contrat d'abord » : le contrat est écrit AVANT le code (il décrit déjà les routes todos que vous
allez écrire). Le test tests/test_docs.py vérifie qu'il décrit toute route réellement exposée par l'application.
Swagger UI est chargée depuis un CDN : le poste doit avoir accès à Internet.
"""

from pathlib import Path

from flask import Blueprint, Response, current_app, send_from_directory

bp = Blueprint("docs", __name__, url_prefix="/api")

_SWAGGER_UI = """<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <title>API Todo : documentation</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.17.14/swagger-ui.css">
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.17.14/swagger-ui-bundle.js"></script>
  <script>SwaggerUIBundle({ url: "/api/openapi.yaml", dom_id: "#swagger-ui" });</script>
</body>
</html>"""


def _docs_dir() -> Path:
    return Path(current_app.root_path).parent / "docs"


@bp.get("/openapi.yaml")
def openapi():
    return send_from_directory(_docs_dir(), "openapi.yaml", mimetype="application/yaml")


@bp.get("/docs")
def swagger_ui():
    return Response(_SWAGGER_UI, mimetype="text/html")
