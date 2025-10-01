# Assistant Ops Reference

This file captures the patterns, environment quirks, and triage playbook that keep future sessions fast and safe. It complements `docs/underwriting_gospel.md` (workflow contract) with the operational context learned the hard way.

---

## 0. First 5 Minutes Checklist

1. **Read config + env**
   - `app/config.py` (look for new settings; `sandbox_mode`, `llm_provider`).
   - `/etc/softmax/api.env` on prod VM for overrides (DB URL, API keys, Gemini key, collateral API key).

2. **Confirm pipeline topology**
   - `app/pipeline/`: active modules are `fuse.py`, `collateral.py`, `parser_adapter.py`, `llm.py`. Anything else is legacy if not referenced.
   - `app/workers/tasks.py` and `app/workers/polling_worker.py` show how fuse+LLM are wired.

3. **Backend & dashboard routes**
   - `app/routes/dashboard.py` (schema for API → dashboard consumers).
   - `frontend/src/pages/*.tsx` for UI expectations (`AdminDashboard`, `BankDashboard`).

4. **Telemetry/observability availability**
   - `app/observability.py` now handles optional OTEL modules. Lack of `OTEL_ENABLED` is fine.

5. **Database sanity**
   - Use `session_scope` to inspect `Job`, `Payload`, `Features`, `Result`, `Audit` counts. On fresh QA runs load simulation output to keep dashboards populated.

---

## 1. Environments & Credentials

| Item | Location | Notes |
| --- | --- | --- |
| Prod env vars | `/etc/softmax/api.env` | Contains DB URL, Redis, Gemini, collateral API key. Use `set -a && source ...` when running scripts. |
| Tenants | `app/db.py` helpers + `scripts/load_sim_jobs.py` | Tenants: `tdb`, `tbf`, `tenant_…` (admin console). Tokens issued via `issue_access_token`. |
| Dashboard OAuth creds | `ADMIN_CREDENTIALS.txt` | Client id/secret/API key generated locally for reference. |
| Simulation fixtures | `mockdata/LoanApplicant_00x.json`, PDFs. |
| Scripts | `scripts/run_simulations.py` (runs pipeline), `scripts/load_sim_jobs.py` (load results into DB). |

**Tip:** after purging jobs run:
```bash
cd /opt/softmax
set -a && source /etc/softmax/api.env && set +a
PYTHONPATH=/opt/softmax /opt/venv/bin/python scripts/run_simulations.py
PYTHONPATH=/opt/softmax /opt/venv/bin/python scripts/load_sim_jobs.py
```
This keeps the dashboard populated with 5 sanitized examples.

---

## 2. LLM Integration

- Production LLM is **Gemini** (`app/pipeline/llm.py`). Sandbox fallback was removed; if you see `LLM provider integration not yet implemented`, the old file is still deployed.
- Checklist when memos disappear:
  1. `sandbox_mode` false and `LLM_PROVIDER` not `sandbox`.
  2. `GEMINI_API_KEY` present in env.
  3. Worker restarted (`sudo systemctl restart softmax-uw-worker`).
  4. Network OK; inspect `/var/log/syslog` or service journal.
- Memo markdown rendered via `MarkdownRenderer` on the dashboard. Confirm API value first before debugging UI.

---

## 3. Collateral & Bank Inputs

- `fuse.py` passes through raw collateral artifacts plus derived summary only. No synthetic `Risk_Score`/Mongolian narrative blocks remain. If you see those, you’re looking at stale features.
- Vehicle flow: ML API (`/api/predict-price/`) → fallback SERP text.
- Real estate: SERP only; stored under `llm_input.collateral.web_search_results`.
- Bank summary: `{ "average_monthly_income_mnt", "statement_period" }`. Big numbers usually mean transactional lines include running balances; check parser rows in `Result.json_tail.parser.rows`.

---

## 4. Database Reset / Seed Recipes

```bash
PYTHONPATH=/opt/softmax /opt/venv/bin/python - <<'PY'
from app.db import session_scope
from app.models import Audit, Result, Features, Payload, Job
with session_scope() as session:
    for model in (Audit, Result, Features, Payload, Job):
        session.query(model).delete()
PY
```
Then rerun simulation + loader (see §1). Dashboard will repopulate automatically.

`/opt/softmax/scripts/load_sim_jobs.py` is safe to run repeatedly; it assigns client IDs `SIM-<TENANT>-NNN`.

---

## 5. Dashboard Rendering Notes

- Use `MarkdownRenderer` (`frontend/src/components/MarkdownRenderer.tsx`) for any memo output. It handles headings, tables, lists, and inline formatting without external packages.
- Admin dashboard exposes raw + processed inputs; bank dashboard hides the `llm_input`. Update `frontend/src/api/client.ts` whenever API shapes change.

---

## 6. Common Pitfalls & Quick Fixes

| Issue | Symptom | Fix |
| --- | --- | --- |
| Gemini stub still deployed | API returns `"error": "LLM provider integration not yet implemented"`. | Sync `/opt/softmax/app/pipeline/llm.py`, restart worker. |
| Dashboard empty | UI shows “No jobs found”. | Run simulation + loader scripts; confirm DB job count. |
| Old synthetic features | `llm_input` contains Mongolian narrative/risk score. | Redeploy `fuse.py`; wipe/reseed DB. |
| Bank parser warnings | Console logs many `ValueError in strToFloat '0 0.00'`. | Harmless. Only log noise; parser still produces averages. |
| OTEL crash | API fails with Prometheus exporter import error. | Ensure latest `app/observability.py` deployed (it handles optional exporter). |

---

## 7. Removed / Deprecated Artifacts

To prevent future confusion the following have been deleted:
- `app/pipeline/rules.py` (and any doc referencing it).
- Legacy simulation logs (`simulation_results.md`, `simulation_*.log`).

Trust the current sources:
- `docs/underwriting_gospel.md` for workflow contract.
- `docs/assistant_reference.md` (this file) for operational context.

---

## 8. Handy Commands

```bash
# Check service health
sudo systemctl status softmax-uw-api --no-pager
sudo systemctl status softmax-uw-worker --no-pager

# Tail worker logs when debugging Gemini or collateral calls
sudo journalctl -u softmax-uw-worker -n 200 -f

# Issue admin token
PYTHONPATH=/opt/softmax /opt/venv/bin/python - <<'PY'
from app.db import session_scope
from app.models import Tenant
from app.security import issue_access_token
with session_scope() as session:
    tenant = session.query(Tenant).filter_by(name='Softmax Admin Console').first()
    print(issue_access_token(tenant, ['dashboard:admin']))
PY
```

Keep this document up to date when new lessons surface.
