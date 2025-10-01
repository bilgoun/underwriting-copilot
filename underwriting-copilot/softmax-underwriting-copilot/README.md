# Softmax Underwriting Copilot

Production-ready underwriting service providing a single ingest API, Celery worker pipeline, and webhook delivery for Mongolian credit memo generation.

## Features
- FastAPI REST API with sandbox/production modes, idempotent ingest, and HMAC request verification.
- Celery + Redis worker pipeline: statement parsing, collateral valuation, feature fusion, LLM memo generation, webhook emission.
- PostgreSQL persistence with encrypted JSON columns for payloads, features, and results.
- OAuth2 client credentials and API key authentication, per-tenant rate limiting, structured logging, Prometheus metrics.
- Docker/Docker Compose for local development; Kubernetes manifests and systemd/cloud-init templates for production deployment.
- CI workflow (GitHub Actions) covering lint, tests, and image builds.

## Quickstart (Local)
1. **Prerequisites**: Docker, Docker Compose, Python 3.11 (optional for direct execution).
2. **Generate keys**:
   ```bash
   python scripts/gen_hmac_secret.py > .hmac_secret
   export ENCRYPTION_KEY=$(python - <<'PY'
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
PY)
   ```
3. **Launch stack**:
   ```bash
   ENCRYPTION_KEY=$ENCRYPTION_KEY docker compose up --build
   ```
4. **Bootstrap database (first run)**:
   ```bash
   docker compose exec api ./scripts/bootstrap_db.sh
   ```
5. **Smoke test**:
   ```bash
   curl -s http://localhost:8080/healthz
   ```

### Running Tests
```bash
python -m pip install -r requirements.txt
export ENCRYPTION_KEY=$(python - <<'PY'
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
PY)
export DATABASE_URL=sqlite+pysqlite:///:memory:
export SANDBOX_MODE=true
pytest -q
```

## Configuration
Key environment variables:

| Variable | Description |
| --- | --- |
| `PORT` | API listening port (default 8080) |
| `DATABASE_URL` | e.g. `postgresql+psycopg://user:pass@host/db` |
| `REDIS_URL` | Celery broker, supports `redis://` and `rediss://` |
| `ENCRYPTION_KEY` | 32-byte urlsafe base64 key for Fernet encryption |
| `SANDBOX_MODE` | `true` for deterministic stubs |
| `TENANT_SECRET` | HMAC key for inbound signatures (per tenant in DB) |
| `WEBHOOK_SECRET` | HMAC key for webhook signatures |
| `LLM_PROVIDER` / `LLM_API_KEY` | Real LLM configuration when not using sandbox |
| `SOFTMAX_COLLATERAL_URL` | Collateral valuation API base URL |
| `COLLATERAL_API_KEY` | API key for collateral valuation requests |

Configuration defaults live in `app/config.py`. All secrets should be provided via environment variables or secret managers.

## API Overview
- `POST /v1/underwrite`: ingest canonical payload, returns job ID. Requires `X-Api-Key`, optional OAuth2 access token, and `X-Signature` HMAC header.
- `GET /v1/jobs/{job_id}`: fetch job status and memo bundle.
- `POST /v1/jobs/pull` / `POST /v1/jobs/complete`: polling worker fallback when Redis is unavailable.
- `POST /v1/webhooks/test`: send signed sample webhook to a target URL.
- `GET /healthz`, `/readyz`, `/metrics`.
- OAuth2 token endpoint: `POST /oauth/token` (client credentials grant).

OpenAPI 3.1 specification: `app/openapi.yaml`.

## Worker Pipeline
1. Download statement PDF (validated by `app/utils/pdf.py`).
2. Parse using `app/pipeline/parser_adapter.py` wrapping bank_parser module (to be provided separately).
3. Call collateral valuation (sandbox stub or real HTTP call) from `app/pipeline/collateral.py`.
4. Fuse Mongolian feature JSON prior to LLM invocation (`app/pipeline/fuse.py`).
5. Generate memo via LLM (`app/pipeline/llm.py`—sandbox stub by default).
6. Persist encrypted payloads/results and emit signed webhook via `app/utils/webhooks.py`.

Metrics exported (Prometheus): `jobs_created_total`, `jobs_failed_total`, `underwrite_duration_seconds`, `parser_seconds`, `collateral_seconds`, `llm_seconds`, `webhook_attempts_total`, `webhook_failures_total`.

## Deployment
### GCP (API service on www.softmax.mn)
1. Build & push container:
   ```bash
   docker build -f Dockerfile.api -t gcr.io/<project>/softmax-uw-api:latest .
   docker push gcr.io/<project>/softmax-uw-api:latest
   ```
2. Prepare secrets (`softmax-uw-secrets`): `database_url`, `redis_url`, `encryption_key`, `redis_password`, `postgres_password`.
3. Apply Kubernetes manifests:
   ```bash
   kubectl apply -f k8s/postgres.yaml
   kubectl apply -f k8s/redis.yaml
   kubectl apply -f k8s/api-deployment.yaml
   ```
4. Configure HTTPS ingress on `www.softmax.mn`, terminate TLS, and forward to `softmax-uw-api` Service port 80.
5. Set up Stackdriver logging & Prometheus scraping of `/metrics` (via ServiceMonitor or sidecar).

### Azure (F16s v2 worker VM)
1. Provision Ubuntu VM (16 vCPU, 32 GB RAM) with fast data disk mounted at `/mnt/softmax_tmp`.
2. Attach network security group: allow SSH (22) from Softmax IPs only, egress to GCP Redis/Postgres endpoints.
3. Use `infra/cloud-init/azure-worker.yaml` during VM creation to install dependencies, create `softmax` user, and register systemd worker service.
4. Drop application code under `/opt/softmax` (e.g. git clone + pip install in `/opt/venv`).
5. Populate `/etc/softmax/worker.env` with `DATABASE_URL`, `REDIS_URL` (TLS `rediss://`), `ENCRYPTION_KEY`, `SANDBOX_MODE=false`.
6. Start worker: `sudo systemctl restart softmax-uw-worker.service`. Monitor via `journalctl -u softmax-uw-worker`.

### Cross-cloud Connectivity
- Prefer Redis TLS endpoint exposed from GCP (allowlist Azure VM public IP); fallback to HTTPS polling worker using `/v1/jobs/pull` and `/v1/jobs/complete`.
- Ensure Postgres accepts Azure worker IP (VPC peering or Cloud SQL Proxy as alternative).
- Set `TMPDIR=/mnt/softmax_tmp` for high I/O parsing.

## Load Testing
Use `scripts/load_test.py` against sandbox:
```bash
python scripts/load_test.py --api http://localhost:8080/v1/underwrite \
  --jobs 100 --api-key <key> --tenant-secret <secret> --tenant-id <tenant>
```
Target results observed on Azure F16s v2 (sandbox mode):
- p95 end-to-end latency `< 20s`
- Failure rate `< 0.5%`

## Observability & Logging
- Structured JSON logs via `structlog`, automatically redacting PII fields.
- Request IDs propagated via `X-Request-Id` header.
- Prometheus metrics available at `/metrics` (configure scraping). Example alert: `webhook_failures_total` > 0.

## CI/CD
GitHub Actions workflow (`.github/workflows/ci.yaml`) executes lint, tests, and Docker builds on every push/PR. Artifacts can be pushed to GHCR/GCR via additional steps.

## Additional Notes
- Place `bank_parser/` package under `app/pipeline/bank_parser/` (kept untouched) to enable production parsing.
- Use `scripts/gen_hmac_secret.py` for tenant/webhook secrets and store hashed API keys via `app.db.hash_api_key` when seeding tenants.
- OAuth clients: store `client_secret` hashed with `app.db.hash_secret` before inserting into `tenants` table.

## Repository Structure
```
app/                FastAPI app, workers, pipeline modules
scripts/            Bootstrap, load testing, secret generation
k8s/                Kubernetes manifests for API, worker, Redis, Postgres
infra/              systemd units and Azure cloud-init
tests/              Unit & integration tests with fixtures
Dockerfile.*        Container builds for API and worker
```
