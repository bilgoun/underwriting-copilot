# Softmax Underwriting Copilot – Agent Runbook

This document captures the current repository layout, operational context, and verified workflows so future Codex/Coding Assistant sessions can come up to speed quickly.

## 1. Repository Snapshot
- Language/runtime: Python 3.11+
- Core stack: FastAPI + Uvicorn API, Celery workers (Redis broker) with optional HTTPS polling fallback, PostgreSQL persistence via SQLAlchemy/Alembic, structlog logging, Prometheus metrics.
- Directory highlights:
  - `app/` – application code
    - `config.py` – environment-driven settings (uses `pydantic_settings`) with `COLLATERAL_API_KEY`, `SOFTMAX_COLLATERAL_URL`, `SANDBOX_MODE`, etc.
    - `routes/` – FastAPI routers (`/v1/underwrite`, `/v1/jobs/*`, `/v1/webhooks/test`, OAuth token endpoint).
    - `workers/` – Celery setup (`celery_app.py`, `tasks.py` pipeline, `polling_worker.py`).
    - `pipeline/` – bank statement parser adapter (`parser_adapter.py`), collateral API client (`collateral.py`), feature fusion (`fuse.py`), LLM memo generation stub (`llm.py`), guardrail rules (`rules.py`).
    - `utils/` – idempotency helper, storage/download, PDF validation, webhook signing/emission, Fernet-based JSON crypto.
    - `models.py` – SQLAlchemy models with encrypted JSON columns for payloads/features/results + audit trail.
  - `mockdata/` – uploaded sample bank statement PDFs.
  - `scripts/` – bootstrap DB, load tester, HMAC secret generator.
  - `infra/` – systemd units and Azure cloud-init for worker host.
  - `k8s/` – manifests for API, worker, Redis, Postgres.
  - `tests/` – unit + integration coverage (integration test relies on sandbox fakes).

## 2. Environment & Secrets
- Required env vars (see `README.md` table): `DATABASE_URL`, `ENCRYPTION_KEY`, `SANDBOX_MODE`, `COLLATERAL_API_KEY`, `SOFTMAX_COLLATERAL_URL`, tenant secrets, etc.
- Collateral valuation:
  - Endpoint: `https://softmax.mn/api/predict-price/`
  - Header: `X-API-KEY: <COLLATERAL_API_KEY>`
  - Current key (PRODUCTION SECRET – **do not commit/echo**): `3SKk08ezxf8LZdqV1E4AtMYrS1RsA33ejVyatjvQL08` (inject via env/secret manager).
  - Sandbox mode (`SANDBOX_MODE=true`) bypasses external call and returns deterministic stub.
  - As of last run, direct call with provided key returned HTTP 403 – verify allowlists/credentials before production use.

## 3. Bank Statement Parser
- Bank parser codebase must live under `app/pipeline/bank_parser/`.
- Adapter signature: `from .bank_parser.registry import detect_bank`.
- Current smoke-test over `mockdata/*.pdf` produced `bank=UNKNOWN` and zero rows – likely requires native deps or updated parser resources on this machine. Ensure bank_parser dependencies (e.g., Tesseract/Poppler) are installed before relying on output.

## 4. Testing & Tooling
- Local unit/integration tests: `pytest -q` (requires packages from `requirements.txt` and env vars; note tests expect sandbox mode and Fernet key).
- Load testing: `scripts/load_test.py` (async POSTs to `/v1/underwrite` with HMAC-signed payloads).
- Celery tasks rely on Redis; polling worker can use `/v1/jobs/pull` and `/v1/jobs/complete` if Redis unavailable.

## 5. SSH / Azure Worker VM Details
- VM type: Azure F16s v2 (16 vCPUs, 32 GB RAM) intended for CPU-heavy bank parsing.
- SSH access command (private key stored locally):
  ```bash
  ssh -i ~/Downloads/softmax-uw-worker-eastus-01-key.pem softmax@20.55.31.2
  ```
- Provisioning steps on first login:
  ```bash
  sudo apt update
  sudo apt -y install python3 python3-venv python3-pip build-essential \
    libjpeg-dev zlib1g-dev libpng-dev libfreetype6-dev \
    libxml2-dev libxslt1-dev ghostscript poppler-utils git curl

  python3 -m venv ~/uw-venv
  source ~/uw-venv/bin/activate
  pip install --upgrade pip wheel

  # Core parsing + data stack
  pip install "pymupdf==1.24.9" "pdfplumber==0.11.0" "pandas==2.2.2" "numpy==1.26.4"

  # Worker + IO tooling
  pip install "requests>=2.32" "redis>=5.0" "rq>=1.15"  # swap in Celery if preferred
  ```
- Ensure `/mnt/softmax_tmp` exists for high-I/O temp files (`TMPDIR` env var should point here). Systemd files in `infra/systemd/` expect virtualenv at `/opt/venv`—adjust paths if using `~/uw-venv` or update unit files accordingly.

## 6. Verification Checklist Before Production Changes
1. Confirm environment variables (especially secrets) configured in deployment.
2. Validate bank parser dependencies (Tesseract/Poppler) installed; rerun parser smoke-test over `mockdata/`.
3. Test collateral API with real key (expect JSON including predicted price/confidence). Resolve any 403s with platform team.
4. Run `pytest -q` locally with sandbox mode to prevent external calls.
5. Update `AGENTS.md` if any steps or infrastructure change.

## 7. Open Issues / Follow-ups
- Collateral API returning 403 despite supplied key – requires investigation (key activation, IP allowlist, payload requirements).
- Bank parser returning empty output on sample PDFs – confirm parser assets, fonts, OCR dependencies, or update `mockdata` with supported formats.
- Expand tests for live pipeline once bank parser & collateral API are confirmed operational.

_Last updated: 2025-09-24T03:03:12Z_
## 8. Current LLM Payload Contract
- Bank statements: run `parser_adapter.parse(pdf_path)` followed by `normalizer.normalize(...)`.
  - Only the average monthly income (MNT) from the normalized bank output is forwarded to the LLM (key: `bankStatement.avgMonthlyIncomeMNT`).
- Collateral valuation: call `https://softmax.mn/api/predict-price/` with the vehicle attributes provided by the fintech client.
  - Use the returned `predicted_price` (MNT) as `collateralCheck.vehicle.estValueMNT`.
  - Compute LTV against the requested loan amount (e.g., 27,000,000 / 59,622,330 ≈ 45.3%).
- Third-party data (social insurance, credit bureau) must be passed as raw JSON payloads without normalization.
- Final LLM input example:
```json
{
  "bankStatement": {
    "avgMonthlyIncomeMNT": 1049758532
  },
  "collateralCheck": {
    "vehicle": {
      "estValueMNT": 59622330,
      "pledged": false,
      "taxDueMNT": 0
    },
    "immovablePropertyFound": false,
    "ltvIfVehicleOnlyPct": 45.3
  },
  "creditBureauRaw": { ... },
  "socialInsuranceRaw": { ... }
}
```
- Document these steps when updating pipelines or onboarding new agents.

