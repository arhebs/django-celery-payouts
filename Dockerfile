# Dockerfile
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=2.2.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="$POETRY_HOME/bin:$PATH"

WORKDIR /app

# Dependencies layer
FROM base AS dependencies
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-interaction --no-ansi --no-root --only main

# Development image
FROM dependencies AS development
RUN poetry install --no-interaction --no-ansi --no-root
COPY . .
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# Production image
FROM dependencies AS production
COPY . .
RUN poetry install --no-interaction --no-ansi --no-root --only main
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
