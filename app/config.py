"""Configuration lue dans l'environnement (fichier .env chargé par Docker Compose)."""

import os


class Config:
    # Corps de requête limités à 1 Mo (OWASP API4 : consommation de ressources)
    MAX_CONTENT_LENGTH = 1024 * 1024

    # --- JWT : signature RS256 (clé privée), vérification (clé publique) ---
    JWT_ISSUER = "https://todo.example.test"
    JWT_TTL_SECONDS = int(os.environ.get("TOKEN_TTL_SECONDS", "3600"))  # courte : un JWT ne se révoque pas facilement
    JWT_PRIVATE_KEY_PATH = os.environ.get("JWT_PRIVATE_KEY_PATH", "/keys/privateKey.pem")
    JWT_PUBLIC_KEY_PATH = os.environ.get("JWT_PUBLIC_KEY_PATH", "/keys/publicKey.pem")
    # Contenu PEM des clés : prioritaire sur le chemin (utilisé par les tests, qui génèrent leurs clés)
    JWT_PRIVATE_KEY: str | None = None
    JWT_PUBLIC_KEY: str | None = None

    # --- Comptes de démonstration (mots de passe lus dans .env) ---
    ADMIN_PASSWORD = os.environ.get("APP_ADMIN_PASSWORD", "")
    USER_PASSWORD = os.environ.get("APP_USER_PASSWORD", "")
