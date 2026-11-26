# Changelog

Toutes les modifications notables apportées à ce projet sont documentées dans ce fichier.
Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/), et ce projet adhère à [Semantic Versioning](https://semver.org/lang/fr/).

## [1.0.0] - 2026-11-24

### Ajouté
- **Routes REST complètes** :
  - `PATCH /api/v1/todos/<id>` : modification partielle d'une tâche (titre, statut `done` ou les deux) avec validation stricte (422 si corps vide ou titre invalide).
  - `DELETE /api/v1/todos/<id>` : suppression d'une tâche avec retour `204 No Content`, réservée exclusivement au rôle `admin`.
  - Filtrage `GET /api/v1/todos?done=true|false` : filtrage par état de complétion (422 si valeur invalide).
- **Sécurisation & RBAC** :
  - Protection de toutes les routes `todos` par jeton JWT Bearer (`@require_auth()`).
  - Contrôle d'accès basé sur les rôles (RBAC) : restriction de la suppression au rôle `admin` (`@require_auth(ROLE_ADMIN)`).
  - Gestion des erreurs 401 (non authentifié) et 403 (action non autorisée) au format d'erreur uniforme `{ "message": "..." }`.
- **Documentation OpenAPI / Swagger** :
  - Mise à jour complète du contrat `docs/openapi.yaml` avec toutes les routes, paramètres, schémas et codes de réponse (200, 201, 204, 401, 403, 404, 422).
  - Support de l'authentification Bearer via le bouton *Authorize* de Swagger UI.
- **Tests automatisés** :
  - Test unitaire de concurrence (`tests/test_project.py`) validant la création simultanée de 100 tâches par 100 threads sans collision d'identifiants ni perte de données.
  - Tests d'API pour `PATCH`, `DELETE`, le filtre `?done=` et les cas de sécurité (401 et 403).
  - Adaptation des tests du TP 3 (`tests/test_todos.py`) avec injection d'authentification valide.
- **Conteneurisation de production** :
  - Cible `prod` dans le `Dockerfile` multi-stage, sans secret embarqué, exécutée sous l'utilisateur non-root `app`.
  - Support du registre local (`registry:2` sur `localhost:5000`).

---

## [0.1.0] - 2026-11-02

### Ajouté
- Squelette initial de l'application Flask (TP 3).
- Routes de démonstration : `GET /api/v1/health` (publique), `POST /api/v1/auth/login` et `GET /api/v1/me` (protégée).
- Stockage initial en mémoire `TodoStore`.
- Routes initiales : `POST /api/v1/todos`, `GET /api/v1/todos`, `GET /api/v1/todos/<id>`.
