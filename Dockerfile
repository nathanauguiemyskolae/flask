# syntax=docker/dockerfile:1

# ---------------------------------------------------------------------------
# Base commune : Python et dépendances d'exécution, utilisateur non root
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS base
ARG UID=1000
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
RUN useradd --create-home --uid "${UID}" app
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

# ---------------------------------------------------------------------------
# Développement : code monté depuis l'hôte, rechargement automatique, outils de test
#
# UN SEUL processus (--workers 1) et plusieurs threads (--threads 4) : les tâches sont gardées en mémoire,
# et chaque processus aurait SA PROPRE mémoire. Les threads, eux, partagent la mémoire du processus.
# ---------------------------------------------------------------------------
FROM base AS dev
COPY requirements-dev.txt .
RUN pip install -r requirements-dev.txt
USER app
EXPOSE 8080
CMD ["gunicorn", "--reload", "--workers", "1", "--threads", "4", "--bind", "0.0.0.0:8080", "--access-logfile", "-", "app:create_app()"]

# ---------------------------------------------------------------------------
# Production : seul le code nécessaire est copié dans l'image
# ---------------------------------------------------------------------------
FROM base AS prod
COPY --chown=app:app app ./app
COPY --chown=app:app docs ./docs
USER app
EXPOSE 8080
CMD ["gunicorn", "--workers", "1", "--threads", "8", "--bind", "0.0.0.0:8080", "--access-logfile", "-", "app:create_app()"]
