# Compte-rendu du TP 3 (Python / Flask) - API REST Todo

**Binôme / Étudiant(e)** : Étudiant ESGI 4ESGI  
**Date** : 2026-11-24  

---

## Vérification de l'implémentation (Étapes 1 à 6)

L'ensemble des composants du TP 3 a été vérifié et respecte le contrat d'API :
1. **Étape 1 & 2** : Le squelette, la gestion centralisée des erreurs (`app/errors.py`), le modèle immuable (`app/models.py`) et l'authentification JWT sont compris et opérationnels.
2. **Étape 3** : La classe `TodoStore` (`app/store.py`) est thread-safe grâce à un verrou `threading.Lock()` englobant les accès à `self._todos` et à `self._next_id`.
3. **Étape 4** : 
   - Le schéma d'entrée `TodoInputSchema` (`app/schemas.py`) valide la présence, la non-vacuité et la limite de 100 caractères du titre, tout en ignorant les champs superflus (`unknown = EXCLUDE`).
   - Les trois routes de `app/routes/todos.py` sont conformes au contrat :
     - `POST /api/v1/todos` crée la tâche, retourne `201 Created` avec l'en-tête `Location: /api/v1/todos/<id>` et l'enveloppe `{ "data": ... }`.
     - `GET /api/v1/todos` retourne la liste ordonnée des tâches avec `200 OK`.
     - `GET /api/v1/todos/<int:todo_id>` retourne la tâche demandée ou lève une `ApiError(404, "Todo not found.")`.
4. **Documentation & Contrat** : L'API correspond au contrat OpenAPI (`docs/openapi.yaml`) et satisfait les tests automatisés (`tests/test_todos.py` et `tests/test_docs.py`).

---

## Réponses aux questions du TP

### Étape 1 : Démarrer le squelette et le comprendre

#### Question 1
> **Quelle différence entre `health.py` et `me.py`, et qu'obtient-on sans jeton sur chacune ?**

- **Différence :**
  - `health.py` est une route **publique** non authentifiée. Elle sert de sonde de supervision/liveness pour vérifier que le service répond.
  - `me.py` est une route **protégée** par le décorateur `@require_auth()`. Elle lit les revendications de l'appelant dans le jeton JWT (`g.claims`) pour indiquer son identité et ses rôles.
- **Résultat sans jeton :**
  - `GET /api/v1/health` : code de statut `200 OK` avec le corps `{"status": "ok"}`.
  - `GET /api/v1/me` : code de statut `401 Unauthorized` avec l'en-tête `WWW-Authenticate: Bearer` et un message d'erreur JSON (`{"message": "Authorization header is missing."}` ou équivalent).

---

#### Question 2
> **Que contient la partie centrale du JWT (`iss`, `upn`, `groups`, `exp`) ? Pourquoi peut-on la lire sans connaître la clé ?**

- **Contenu de la partie centrale (Payload / Claims) :**
  - `iss` (*issuer*) : l'émetteur du jeton (l'API d'authentification).
  - `upn` (*user principal name*) : le nom d'utilisateur / identifiant du porteur du jeton (ex. `admin` ou `user`).
  - `groups` : la liste des groupes ou rôles de l'utilisateur (ex. `["admin"]`).
  - `exp` (*expiration time*) : le timestamp Unix marquant l'expiration du jeton.
- **Pourquoi peut-on la lire sans connaître la clé ?**
  - Le JWT n'est **pas chiffré** mais simplement encodé en **Base64URL** (format lisible après décodage standard).
  - La clé secrète/privée ne sert pas à masquer les données, mais à **calculer la signature** (troisième partie du jeton). Cette signature garantit l'**intégrité** et l'**authenticité** du jeton, permettant au serveur de s'assurer qu'il n'a pas été modifié par un tiers.

---

#### Question 3
> **Sur quelle(s) adresse(s) l'API est-elle joignable ? Regardez la ligne `ports:` de `docker-compose.yml`.**

- Dans `docker-compose.yml`, la directive est :
  ```yaml
  ports:
    - "127.0.0.1:8080:8080"
  ```
- L'API est joignable exclusivement sur l'adresse de boucle locale (**loopback**) `127.0.0.1` (ou `localhost`), sur le port **8080** (`http://127.0.0.1:8080` ou `http://localhost:8080`).
- Elle n'est **pas exposée** sur les autres interfaces réseau de la machine hôte (LAN/Wi-Fi), ce qui évite toute exposition involontaire sur le réseau externe.

---

### Étape 2 : Comprendre le modèle et la gestion des erreurs

#### Question 4
> **Pourquoi une réponse 500 ne contient-elle jamais la trace de l'exception, alors qu'elle est écrite dans les journaux (`docker compose logs api`) ?**

- **Sécurité (prévention des fuites d'informations) :** La stack trace (trace d'exécution) contient des informations sensibles sur l'environnement interne du serveur (chemins de fichiers sur le disque, versions des bibliothèques utilisées, logique du code, requêtes internes). Renvoyer ces informations à un client ou à un attaquant potentiel facilite l'exploitation de vulnérabilités.
- **Séparation des rôles :**
  - Le **client** doit recevoir un message d'erreur générique standard (ex. `{"message": "Server Error."}`) sans détail d'implémentation.
  - Les **administrateurs et développeurs** ont accès aux journaux internes (`docker compose logs api`) pour investiguer et corriger l'incident.

---

### Étape 3 : Le stockage en mémoire

#### Question 5
> **Que se passe-t-il pour les tâches quand vous exécutez `docker compose restart api` ? Faites l'essai.**

- Toutes les tâches créées sont **définitivement perdues**.
- **Raison :** Les tâches sont stockées en mémoire vive (RAM) dans le dictionnaire `self._todos` du singleton `TodoStore`. Comme il n'y a pas de base de données ni de persistance sur disque, redémarrer le conteneur ou le processus vide la mémoire et réinitialise l'état (`_todos = {}`, `_next_id = 1`).

---

#### Question 6
> **Pourquoi ne peut-on lancer qu'un seul processus de cette API ? Faites le lien avec la contrainte « sans état » de REST (chapitre 1, section 1.4).**

- **Mémoire isolée par processus :** Sous un système d'exploitation, chaque processus possède son propre espace d'adressage mémoire. Si gunicorn démarrait avec 4 workers (4 processus), une tâche créée sur le processus 1 n'existerait pas dans la mémoire des processus 2, 3 et 4. Une requête suivante de lecture `GET /todos/1` arrivant sur le processus 2 renverrait alors une erreur 404.
- **Lien avec la contrainte REST « Stateless » (Sans état) :**
  - La contrainte stateless impose que le serveur ne conserve aucun état client entre les requêtes en mémoire locale, afin de permettre le passage à l'échelle horizontal (*horizontal scaling* / équilibrage de charge entre plusieurs instances).
  - Dans notre TP, l'état réside dans la mémoire locale de l'instance unique, ce qui brise cette indépendance. Pour respecter pleinement la contrainte stateless en production multi-processus, l'état doit être délégué à une base de données ou un cache partagé (PostgreSQL, Redis, etc.).

---

### Étape 4 : Les trois routes

#### Question 7
> **Pourquoi 422 et non 400 pour un titre vide ? Pourquoi 404 et non 200 avec un champ vide pour une tâche inconnue ?**

- **422 (Unprocessable Entity) vs 400 (Bad Request) :**
  - `400 Bad Request` signale une syntaxe HTTP ou JSON invalide (ex. JSON tronqué, mauvais encodage).
  - `422 Unprocessable Entity` indique que le JSON est syntaxiquement correct et a pu être décodé, mais que son contenu ne respecte pas les règles de validation sémantique ou métier (ex. titre vide ou trop long).
- **404 (Not Found) vs 200 avec champ vide :**
  - L'URI `/api/v1/todos/{id}` référence une ressource précise. Si l'identifiant n'existe pas, la ressource est absente : le statut sémantique universel en REST/HTTP est `404 Not Found`.
  - Répondre `200 OK` avec un corps vide indiquerait faussement que la requête a réussi et obligerait le client à implémenter une logique complexe d'inspection du corps au lieu de se fier au code de statut HTTP standard.

---

#### Question 8
> **`GET /todos` est-elle sûre et idempotente ? `POST /todos` l'est-elle ? Rappelez les définitions (chapitre 1, section 1.6).**

- **Définitions :**
  - **Sûre (Safe) :** Une méthode est sûre si son exécution ne modifie pas l'état du serveur (lecture seule, sans effet de bord).
  - **Idempotente :** Une méthode est idempotente si son exécution répétée avec les mêmes paramètres produit exactement le même état final sur le serveur qu'une exécution unique.
- **Analyse des deux routes :**
  - `GET /todos` : **Sûre et idempotente**. Elle n'altère aucune donnée et des appels successifs laissent l'état du serveur inchangé.
  - `POST /todos` : **Ni sûre, ni idempotente**. Elle altère l'état du serveur en créant une nouvelle ressource à chaque appel (`self._next_id += 1`). Exécuter 3 fois la même requête crée 3 tâches distinctes avec 3 identifiants différents.

---

### Étape 6 : Bilan

#### Question 9
> **Quelles routes manque-t-il, selon vous, pour que cette API soit complète ? Lesquelles seraient idempotentes ?**

Pour fournir un cycle de vie complet (CRUD) conforme aux standards REST, il manque :
1. `PUT /api/v1/todos/{id}` : Remplacement complet d'une tâche existante (**Idempotente** : répéter le remplacement avec les mêmes valeurs laisse la ressource dans le même état).
2. `PATCH /api/v1/todos/{id}` : Modification partielle (ex. `{ "done": true }`) (**Idempotente** dans le cas où l'on fixe un état absolu comme `done: true`).
3. `DELETE /api/v1/todos/{id}` : Suppression d'une tâche (**Idempotente** : après le premier appel, la ressource n'existe plus ; les appels subséquents aboutissent au même état final).
4. `GET /api/v1/todos?done=true|false` : Filtrage par état d'avancement (**Sûre et idempotente**).
