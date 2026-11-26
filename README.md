# API REST Todo - ESGI 4-SRC (Projet d'Administration Système)

API REST complète de gestion de tâches pour l'exploitation système d'une PME.
Développée avec Python (Flask), marshmallow, PyJWT (RS256), gunicorn et Swagger UI.

---

## 1. Démarrage depuis zéro (Développement)

```bash
# 1. Cloner le dépôt et copier les variables d'environnement
cp .env.example .env

# 2. Renseigner les mots de passe dans .env :
# APP_ADMIN_PASSWORD=VotreMotDePasseAdmin
# APP_USER_PASSWORD=VotreMotDePasseUser

# 3. Démarrer la stack de développement
docker compose up -d --build

# 4. Suivre les journaux jusqu'à l'écoute sur le port 8080
docker compose logs -f api
```

| Point d'accès | URL | Description |
| :--- | :--- | :--- |
| **Santé** | `http://localhost:8080/api/v1/health` | Sonde de supervision (route publique) |
| **Documentation Swagger** | `http://localhost:8080/api/docs` | Swagger UI interactif (Bouton *Authorize* pour tester avec un JWT) |
| **Contrat OpenAPI** | `http://localhost:8080/api/openapi.yaml` | Spécification brute OpenAPI 3.0 |

---

## 2. Variables d'environnement & Comptes de démonstration

Le fichier `.env` configure les identifiants initiaux des utilisateurs :
- `APP_ADMIN_PASSWORD` : mot de passe du compte `admin` (rôles : `["admin"]`)
- `APP_USER_PASSWORD` : mot de passe du compte `user` (rôles : `["user"]`)

Les comptes disponibles sont :
1. **Administrateur** (`admin`) : accès complet (créer, lire, modifier et **supprimer** les tâches).
2. **Utilisateur standard** (`user`) : accès en consultation, création et modification (la suppression lui est refusée avec une erreur `403 Forbidden`).

---

## 3. Lancement des tests automatisés & Newman

### Tests Pytest (dans le conteneur)
```bash
# Exécuter tous les tests (socle, TP 3 et tests complémentaires du projet)
docker compose run --rm tests pytest

# Exécuter uniquement les tests complémentaires du projet
docker compose run --rm tests pytest tests/test_project.py

# Vérifier la stricte conformité au contrat OpenAPI
docker compose run --rm tests pytest tests/test_docs.py
```

### Exécution de la collection Postman avec Newman
```bash
# Lancement de la collection via l'outil en ligne de commande Newman
npx newman run postman/todo-api.postman_collection.json \
  -e postman/todo-local.postman_environment.json \
  --env-var "admin_password=$APP_ADMIN_PASSWORD"
```

---

## 4. Publication de l'image de production

L'image de production utilise un Dockerfile multi-stage (`target: prod`), s'exécute sous un utilisateur non-root (`USER app`) et n'embarque aucun secret.

```bash
# 1. Démarrer le registre local
docker run -d --name registry -p 127.0.0.1:5000:5000 registry:2

# 2. Construire l'image de production avec son tag versionné
docker build --target prod -t todo-api:1.0.0 .

# 3. Tagger et pousser vers le registre local
docker tag todo-api:1.0.0 localhost:5000/todo-api:1.0.0
docker push localhost:5000/todo-api:1.0.0

# 4. Vérifier la présence de l'image dans le catalogue de l'API du registre
curl -s http://localhost:5000/v2/_catalog
curl -s http://localhost:5000/v2/todo-api/tags/list

# 5. Exécution autonome de l'image de production
docker run --rm -d \
  --name todo-api-prod \
  -p 127.0.0.1:8080:8080 \
  --env-file .env \
  -e JWT_PUBLIC_KEY_PATH=/keys/publicKey.pem \
  -e JWT_PRIVATE_KEY_PATH=/keys/privateKey.pem \
  -v todo-flask_jwt-keys:/keys:ro \
  localhost:5000/todo-api:1.0.0
```

---

## 5. Limites connues de l'implémentation actuelle

1. **Stockage volatil en mémoire vive (RAM)** :
   - Les tâches vivent dans le dictionnaire du singleton `TodoStore`.
   - Tout arrêt ou redémarrage du conteneur réinitialise les données (`_todos = {}`).
2. **Mono-processus obligatoire (`--workers 1`)** :
   - Chaque processus de l'OS possède sa propre mémoire isolée.
   - Lancer plusieurs workers gunicorn entraînerait des désynchronisations de données (une tâche créée sur le worker 1 serait introuvable sur le worker 2).

---

## 6. Passer en production (Architecture Cible & Scalabilité)

Pour exposer cette API sur Internet de manière sécurisée et scalable dans un cadre d'entreprise, les évolutions architecturales suivantes doivent être déployées :

1. **Persistance partagée (Base de données relationnelle)** :
   - Remplacer le `TodoStore` en mémoire par **PostgreSQL** avec un pool de connexions (SQLAlchemy / PgBouncer).
   - Les tâches persistent aux pannes et redémarrages.
2. **Stateless réel & Scalabilité horizontale (Multi-workers & Kubernetes)** :
   - Une fois la persistance externalisée en BDD, l'API devient 100 % **sans état** (*stateless*).
   - Gunicorn peut être configuré avec `(2 x vCPU) + 1` workers.
   - L'API peut être répliquée sur plusieurs conteneurs/pods derrière un répartiteur de charge avec un mécanisme d'auto-scaling horizontal (HPA).
3. **Sécurisation en bordure de réseau (Edge / Reverse Proxy)** :
   - Déploiement d'un Reverse Proxy (Nginx, Traefik, HAProxy ou Ingress Controller).
   - Chiffrement systématique via terminaison TLS/HTTPS (certificats Let's Encrypt / cert-manager).
   - En-têtes de sécurité HTTP stricts (HSTS, CSP, X-Frame-Options).
4. **Gestion centralisée des identités et rotation des clés** :
   - Délégation de l'émission des JWT à un fournisseur d'identité dédié (Keycloak, Auth0 / OIDC).
   - Vérification des clés via un endpoint standard **JWKS** (`.well-known/jwks.json`) ou injection des clés via un Secret Manager (HashiCorp Vault, AWS Secrets Manager) avec rotation périodique.
5. **Rate Limiting & Protection contre les abus** :
   - Limitation de débit (Rate Limiting) adossée à un cache Redis distribué (ex. 100 requêtes/minute par adresse IP ou par jeton), renvoyant le code HTTP `429 Too Many Requests`.
6. **Observabilité** :
   - Export de métriques Prometheus (`/metrics`) supervisées avec Grafana (taux d'erreurs 4xx/5xx, latence p95/p99).
   - Traçabilité et corrélation des requêtes avec des journaux JSON centralisés (Loki / ELK).
