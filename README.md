# Payout Management Service

A small payout management API built with **Django 4.2**, **Django REST Framework**, and **Celery** for asynchronous
processing. The service exposes a single `/api/payouts/` resource that lets clients create payout requests, track their
status, and update or delete them while a Celery worker performs the background processing.

The project is intentionally structured to showcase clean, production-style backend practices with modern Python
tooling: Poetry, type hints, Ruff, mypy, pytest, Docker, and GitHub Actions.

---

## Features

- Payout model with:
    - UUID primary key
    - `amount` as `DecimalField(max_digits=12, decimal_places=2)`
    - `currency` enum: `USD`, `EUR`, `GBP`, `RUB`
    - `recipient_details` JSON payload requiring an `account_number`
    - Status machine: `PENDING → PROCESSING → COMPLETED | FAILED`
- REST API at `/api/payouts/` with:
    - `POST /api/payouts/` – create payout, enqueue Celery task
    - `GET /api/payouts/` – paginated list with filtering
    - `GET /api/payouts/{id}/` – retrieve a single payout
    - `PATCH /api/payouts/{id}/` – partial update **only when status is `PENDING`**
    - `DELETE /api/payouts/{id}/` – hard delete (simple for this demo)
- Celery task that:
    - Moves status from `PENDING` → `PROCESSING`
    - Simulates an external call with a 5‑second delay
    - Randomly fails ~10% of the time and retries with backoff
    - Finishes as `COMPLETED` or `FAILED`
- Filtering and pagination:
    - Filter by `status`, `currency`, amount range, and created_at range
    - Standard DRF page‑number pagination
- API documentation:
    - OpenAPI schema at `/api/schema/`
    - Swagger UI at `/api/docs/`
    - ReDoc UI at `/api/redoc/`
- Tooling:
    - Poetry for dependency management
    - Ruff + mypy for linting and type checking
    - pytest + pytest‑django for tests
    - Docker + docker compose for local orchestration
    - GitHub Actions CI running lint + tests

---

## Project Layout

Key files and directories:

```text
.
├── config/                  # Django project settings, URLs, celery app
│   ├── celery.py
│   ├── urls.py
│   └── settings/
│       ├── base.py
│       ├── local.py
│       ├── production.py
│       └── test.py
├── apps/
│   └── payouts/
│       ├── admin.py
│       ├── apps.py
│       ├── filters.py
│       ├── models.py
│       ├── serializers.py
│       ├── services.py
│       ├── tasks.py
│       ├── urls.py
│       ├── views.py
│       └── tests/
├── Dockerfile
├── docker-compose.yml
├── docker-compose.override.yml
├── Makefile
├── pyproject.toml
├── pytest.ini
└── README.md
```

---

## Local Development (Poetry + Django)

This mode runs everything directly on your machine using SQLite (for tests) and whatever Postgres/Redis you have
available for development.

### Prerequisites

- Python **3.11+**
- Poetry installed
- PostgreSQL and Redis available locally _or_ via Docker (see next section)

### Setup

1. Install dependencies:

   ```bash
   poetry install
   ```

2. Create a `.env` file based on `.env.example` and set at least:

   ```bash
   SECRET_KEY=change-me
   DEBUG=true
   DATABASE_URL=postgres://postgres:postgres@localhost:5432/django_celery_payouts
   REDIS_URL=redis://localhost:6379/0
   CELERY_BROKER_URL=${REDIS_URL}
   CELERY_RESULT_BACKEND=${REDIS_URL}
   ```

3. Apply migrations:

   ```bash
   poetry run python manage.py migrate
   ```

4. Run the development server:

   ```bash
   poetry run python manage.py runserver
   ```

5. Run the Celery worker in a separate terminal:

   ```bash
   poetry run celery -A config worker -l info
   ```

The API will be available at <http://localhost:8000>.

---

## Docker‑Based Setup

The repository includes a Dockerized stack for local development:

- `web`: Django app (dev server)
- `celery`: Celery worker
- `db`: PostgreSQL 15
- `redis`: Redis 7

### Quick start with docker compose

From the project root:

```bash
docker compose up -d
docker compose exec web python manage.py migrate
```

This will:

- Build the images
- Start all services
- Run migrations inside the `web` container

Once running:

- API: <http://localhost:8000/api/payouts/>
- Swagger UI: <http://localhost:8000/api/docs/>
- ReDoc: <http://localhost:8000/api/redoc/>

To stop the stack:

```bash
docker compose down
```

---

## Makefile Commands

The `Makefile` wraps common docker compose commands. By default it uses `docker compose` (v2).

```bash
make up          # Build and start all services
make down        # Stop and remove containers
make build       # Rebuild images
make migrate     # Run Django migrations
make makemigrations  # Create new migrations
make shell       # Django shell inside web container
make worker      # Tail Celery worker logs
make logs        # Tail all service logs
make test        # Run pytest in web container
make lint        # Run Ruff linting in web container
make format      # Run Ruff format (if configured)
make clean       # Remove containers, volumes, and images related to this project
```

These commands assume you have Docker and docker compose v2 installed.

---

## API Overview

### Base URL

- Local development / Docker: `http://localhost:8000`
- API base path: `/api/payouts/`

### Payout representation

Example JSON for a payout:

```json
{
  "id": "fb03bfe4-cccd-49fa-ba07-758be9468cb2",
  "amount": "100.00",
  "currency": "USD",
  "recipient_details": {
    "account_number": "1234567890"
  },
  "status": "PENDING",
  "description": "Docker test payout",
  "created_at": "2025-12-03T18:30:55.108842Z",
  "updated_at": "2025-12-03T18:30:55.108859Z"
}
```

Fields:

- `id` (read‑only): UUID primary key
- `amount` (required): decimal string, > 0 and ≤ configured max
- `currency` (required): one of `USD`, `EUR`, `GBP`, `RUB`
- `recipient_details` (required): JSON object that **must** contain `account_number`
- `status` (read‑only): `PENDING`, `PROCESSING`, `COMPLETED`, or `FAILED`
- `description` (optional): free‑form text
- `created_at`, `updated_at` (read‑only): ISO 8601 timestamps

### Endpoints

#### `POST /api/payouts/` – Create payout

Request body:

```json
{
  "amount": "250.00",
  "currency": "EUR",
  "recipient_details": {
    "account_number": "DE89370400440532013000",
    "bank_name": "Deutsche Bank"
  },
  "description": "Contractor payment - March 2025"
}
```

Behaviour:

- Returns `201 Created` with `status: "PENDING"`.
- Schedules the Celery task to process the payout asynchronously.

#### `GET /api/payouts/` – List payouts

Query parameters:

- `status`: filter by status (`PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`)
- `currency`: filter by currency
- `created_after`, `created_before`: ISO 8601 timestamps
- `min_amount`, `max_amount`: decimal strings

Paginated response (standard DRF page‑number format).

#### `GET /api/payouts/{id}/` – Retrieve payout

- Returns `200 OK` with the payout representation.
- Returns `404 Not Found` if the payout does not exist.

#### `PATCH /api/payouts/{id}/` – Update payout (PENDING only)

Editable fields:

- `amount`
- `currency`
- `recipient_details`
- `description`

If the payout is not in `PENDING` status, the API returns:

- `403 Forbidden` with `{"detail": "Only PENDING payouts can be updated."}`

#### `DELETE /api/payouts/{id}/` – Delete payout

- Deletes the payout row from the database.
- Returns `204 No Content` on success.
- In a real production system you would likely use soft‑delete instead.

---

## Payout Processing Flow

1. Client sends `POST /api/payouts/` with a valid body.
2. API creates a `Payout` with `status=PENDING`.
3. On transaction commit, the service layer enqueues the Celery task.
4. Celery worker:
    - Locks the payout row in the database.
    - Sets `status=PROCESSING`.
    - Sleeps for 5 seconds to simulate an external integration.
    - With ~10% probability, raises a processing error and retries (up to 3 times).
    - On success, sets `status=COMPLETED`.
    - On permanent failure (after retries), the custom task class marks the payout as `FAILED`.
5. Client can poll `GET /api/payouts/{id}/` to see status changes.

Status transitions:

```text
PENDING → PROCESSING → COMPLETED
        └────────────→ FAILED
```

The `status` field is **not** writable via the API; it is fully controlled by the system and Celery worker.

---

## Environment Variables

The application is configured via environment variables (typically set in `.env` for local development or via your
deployment platform).

Important variables:

- `SECRET_KEY` – Django secret key (required in non‑debug environments)
- `DEBUG` – `"true"` / `"false"` (string, case‑insensitive)
- `ALLOWED_HOSTS` – comma‑separated list of allowed hosts
- `DATABASE_URL` – database connection string, e.g.:
    - `postgres://user:password@host:5432/dbname`
- `REDIS_URL` – Redis connection string, e.g.:
    - `redis://redis:6379/0`
- `CELERY_BROKER_URL` – broker URL (defaults to `REDIS_URL` if not set)
- `CELERY_RESULT_BACKEND` – result backend (defaults to `REDIS_URL` if not set)

---

## Running Tests and Linters

### Locally (without Docker)

From the project root:

```bash
poetry run ruff check .
poetry run mypy apps/
poetry run pytest -v
```

### Inside Docker

With the stack running (`docker compose up -d`):

```bash
docker compose exec web ruff check .
docker compose exec web mypy apps/
docker compose exec web pytest -v
```

Or use the Makefile:

```bash
make lint
make test
```

---

## Verification Checklist

To verify that the full stack works end‑to‑end:

1. Start the Docker stack and run migrations (or use the Makefile):

   ```bash
   docker compose up -d
   docker compose exec web python manage.py migrate --noinput
   # or
   make up
   make migrate
   ```

2. Run the automated verification script:

   ```bash
   bash scripts/verify_setup.sh
   ```

   This script will:

    - Ensure services are running
    - Create a test payout via the API
    - Wait for the Celery worker to process it and print the before/after payloads
    - Check that the API docs endpoints respond with HTTP 200
    - Execute the test suite with coverage inside the `web` container

3. Optionally, open the docs in a browser:

    - Swagger UI: <http://localhost:8000/api/docs/>
    - ReDoc: <http://localhost:8000/api/redoc/>

---

## Production Notes & Limitations

This repository is optimized as a test project and reference implementation. A production deployment would typically add
or change the following:

- **Authentication & authorization** – e.g. JWT or session auth for all endpoints.
- **Soft delete** and audit trails for payouts instead of hard delete.
- **Idempotency keys** for payout creation to avoid duplicates.
- **Stronger validation** of `recipient_details` (country‑specific formats, bank details, etc.).
- **Real payment provider integration** instead of the 5‑second sleep.
- **Observability**: structured logging, metrics, tracing, and alerts.
- **Horizontal scaling**: multiple web and Celery workers behind a load balancer.

Those aspects are intentionally out of scope here but the current structure is designed so they can be added cleanly.

### Known Areas for Improvement

The current implementation deliberately keeps some aspects simple for the purposes of the test task:

- **Security** – Containers run as root in the Docker images. In production, the images should be adjusted to run the
  Django and Celery processes as a non‑privileged user.
- **Observability** – Logging uses the standard Python logging stack. For real deployments, structured logging
  (for example JSON logs via `structlog` or similar) would make ingestion into observability tooling much easier.
- **API semantics** – Status‑based update errors currently return `403 Forbidden`. It may be preferable to use
  `409 Conflict` to signal that the requested state transition is invalid given the current resource state.

---

## CI Pipeline

The project includes a GitHub Actions workflow that runs on pushes and pull requests:

- Installs dependencies via Poetry
- Starts PostgreSQL and Redis services
- Waits for Postgres and applies migrations
- Runs:
    - `ruff check .`
    - `mypy apps/`
    - `pytest -v --cov=apps --cov-report=term-missing`

You can exercise the same workflow locally using the `act` CLI if desired.

---

## Production Deployment Strategy

To deploy this service in a real production environment, a containerized approach on a managed cloud provider (such as
AWS) works well.

### Infrastructure Requirements

- **Compute**: AWS ECS (Fargate) or Kubernetes (EKS) to run containers without managing servers.
- **Database**: Managed PostgreSQL (for example AWS RDS) for automated backups and high availability.
- **Broker/Cache**: Managed Redis (for example AWS ElastiCache).
- **Load Balancer**: Application load balancer for SSL termination and routing to web containers.
- **Secrets**: Secret manager or parameter store (for example AWS Secrets Manager or SSM Parameter Store) for secure
  configuration.

### Deployment Workflow

1. **Build** – CI builds the Docker image from the `production` stage of the `Dockerfile` and pushes it to a container
   registry (for example AWS ECR).
2. **Migrations** – a dedicated job or init‑container runs `python manage.py migrate` against the managed PostgreSQL
   instance before the new version is marked healthy.
3. **Web service** – deployed as a scalable service running Gunicorn
   (`gunicorn config.wsgi:application --bind 0.0.0.0:8000`), behind the load balancer.
4. **Worker service** – deployed as a separate service running the Celery worker
   (`celery -A config worker -l info`), with autoscaling based on queue depth or CPU usage.
5. **Static files** – collected with `python manage.py collectstatic` and served from an object store (for example S3)
   fronted by a CDN (for example CloudFront).

### Environment Preparation

1. Provision network infrastructure (VPC, private subnets, security groups).
2. Launch managed PostgreSQL and Redis instances inside the VPC.
3. Create target groups and an application load balancer pointing to the web service.
4. Configure environment variables (`DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, `ALLOWED_HOSTS`, etc.) in the task or
   pod definitions, sourcing sensitive values from the secrets store.

---

## License

This project is provided for evaluation and learning purposes. Use and adapt it within the constraints of your own
organization or exercise requirements.
