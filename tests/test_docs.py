"""Documentation : le contrat ne ment pas. Chaque route exposée par l'application figure dans docs/openapi.yaml.
Vert dès le départ, et il le reste quand vous ajoutez des routes... à condition de les documenter."""

import re

import yaml


def _normalize(path: str) -> str:
    return re.sub(r"<[^>]+>|\{[^}]+\}", "{}", path)


def test_contract_covers_every_exposed_route(app, client):
    spec = yaml.safe_load(client.get("/api/openapi.yaml").data)
    documented = {(_normalize(path), method.upper())
                  for path, operations in spec["paths"].items()
                  for method in operations if method != "parameters"}

    for rule in app.url_map.iter_rules():
        if not rule.rule.startswith("/api/v1/"):
            continue
        for method in rule.methods - {"HEAD", "OPTIONS"}:
            assert (_normalize(rule.rule), method) in documented, f"{method} {rule.rule} non documentée"
