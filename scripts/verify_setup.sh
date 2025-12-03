#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${PROJECT_ROOT}"

BASE_URL="${BASE_URL:-http://localhost:8000}"

echo "==> Bringing up Docker services"
docker compose up -d

echo "==> Applying database migrations"
docker compose exec web python manage.py migrate --noinput

echo "==> Waiting for web API to become available at ${BASE_URL}"
for _ in {1..20}; do
  if curl -s "${BASE_URL}/api/payouts/" >/dev/null 2>&1; then
    echo "API is reachable."
    break
  fi
  echo "API not ready yet, retrying..."
  sleep 2
done

echo "==> Creating a test payout via API"
CREATE_RESPONSE="$(
  curl -s \
    -X POST "${BASE_URL}/api/payouts/" \
    -H "Content-Type: application/json" \
    -d '{
          "amount": "100.00",
          "currency": "USD",
          "recipient_details": { "account_number": "1234567890" },
          "description": "Verification payout"
        }'
)"

if [[ -z "${CREATE_RESPONSE}" ]]; then
  echo "ERROR: Empty response when creating payout."
  exit 1
fi

PAYOUT_ID="$(
  CREATE_RESPONSE="${CREATE_RESPONSE}" python - << 'PY'
import json
import os

data = json.loads(os.environ["CREATE_RESPONSE"])
print(data.get("id", ""))
PY
)"

if [[ -z "${PAYOUT_ID}" ]]; then
  echo "ERROR: Could not extract payout id from response:"
  echo "${CREATE_RESPONSE}"
  exit 1
fi

echo "Created payout with id: ${PAYOUT_ID}"

echo "==> Fetching payout immediately after creation"
curl -s "${BASE_URL}/api/payouts/${PAYOUT_ID}/" | python -m json.tool || true

echo "==> Waiting for Celery worker to process payout (this may take a few seconds)..."
sleep 7

echo "==> Fetching payout after processing delay"
curl -s "${BASE_URL}/api/payouts/${PAYOUT_ID}/" | python -m json.tool || true

echo "==> Checking API documentation endpoints"
SCHEMA_STATUS="$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/api/schema/")"
DOCS_STATUS="$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/api/docs/")"

echo "Schema endpoint status: ${SCHEMA_STATUS}"
echo "Docs endpoint status:   ${DOCS_STATUS}"

if [[ "${SCHEMA_STATUS}" != "200" || "${DOCS_STATUS}" != "200" ]]; then
  echo "ERROR: One or more documentation endpoints did not return HTTP 200."
  exit 1
fi

echo "==> Running test suite inside web container"
docker compose exec web pytest -v --cov=apps --cov-report=term-missing

echo "==> Verification completed successfully."

