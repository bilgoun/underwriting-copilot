# Observability & Monitoring

This service now ships with a full OpenTelemetry-based observability stack that tracks API health, worker throughput, LLM behaviour, and underwriting KPIs. The stack is designed so banks get a self-service view of their workloads while the Softmax operations team retains visibility into pipeline health without direct access to customer PII.

## Architecture

```
API / Worker / Simulation jobs
        │ (OTLP)
        ▼
OpenTelemetry Collector ──► Prometheus (metrics)
        │                 └─► Grafana dashboards
        ├─► Tempo (traces) ─┐
        └─► Loki  (logs) ───┘
```

* **Instrumentation** – FastAPI, Celery tasks, outbound HTTP calls, and the simulation driver call `init_observability()` when `OTEL_ENABLED=true`. Custom meters expose underwriting KPIs (queue depth, LLM latency, job failures) through OpenTelemetry metrics.
* **Collector** – `otel-collector` receives OTLP logs/metrics/traces from every component and fan-outs to Prometheus, Tempo, and Loki. Built-in batch and memory limiters protect the pipeline.
* **Dashboards** – Grafana auto-provisions two dashboards:
  * `Tenant Underwriting Overview` shows per-tenant latency, throughput, and failure rate. Use the tenant selector to scope to a single bank.
  * `Operator Observability` highlights global queue depth, API error rates, and tenant-level throughput for the ops team.
* **Traces & Logs** – Tempo stores spans for underwriting pipelines (parser, collateral, LLM stages). Loki ingests structured JSON logs from structlog with PII masking.

## Running locally

1. Export an encryption key and (optionally) an LLM API key.
2. Start the stack:

   ```bash
   docker compose up --build
   ```

3. The following ports are exposed:
   * API – `http://localhost:8080`
   * Grafana – `http://localhost:3000` (`admin` / `admin` by default, change in `docker-compose.yaml`).
   * Prometheus – `http://localhost:9090`
   * Tempo – `http://localhost:3200`
   * Loki – `http://localhost:3100`

4. To opt-in from any runtime process (including workers deployed outside Docker), set:

   ```bash
   export OTEL_ENABLED=true
   export OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318  # or the managed collector endpoint
   export OTEL_SERVICE_NAME=softmax-underwriting-api  # override per component
   export OTEL_SERVICE_NAMESPACE=softmax-underwriting
   ```

If `OTEL_ENABLED` is false, instrumentation falls back silently without failing the service.

## Alerting hooks

Prometheus now loads `infra/monitoring/prometheus/alerts.yml` with ready-made rules:

| Alert | Condition | Default | Suggested Action |
| --- | --- | --- | --- |
| `HighHttpErrorRate` | 5 minute 5xx rate > 5% | 5 minutes | Inspect API traces in Tempo, drill into failing endpoints per tenant |
| `QueueBacklogGrowing` | Queue depth > 25 for 10 minutes | 10 minutes | Scale workers or investigate upstream outages |
| `LlmLatencyHigh` | p95 LLM latency > 30s for 10 minutes | 10 minutes | Check provider health, fall back to cached memo strategy |

To wire alerts into PagerDuty/Opsgenie, deploy Alertmanager and point Prometheus to it via `--alertmanager.url` or Edit `infra/monitoring/prometheus/prometheus.yml` accordingly.

## Dashboard API access

The API exposes role-aware dashboard endpoints under `/v1/dashboard/*`:

| Endpoint | Scope | Description |
| --- | --- | --- |
| `GET /v1/dashboard/tenant/jobs` | `dashboard:read` | Paginated job summaries, plus aggregate stats for the calling bank |
| `GET /v1/dashboard/tenant/jobs/{job_id}` | `dashboard:read` | Detailed record with raw payload, fused features, LLM output, and audit history |
| `GET /v1/dashboard/tenant/summary` | `dashboard:read` | Rolling metrics for the past N hours |
| `GET /v1/dashboard/admin/jobs` | `dashboard:admin` | Cross-tenant job list for operators |
| `GET /v1/dashboard/admin/jobs/{job_id}` | `dashboard:admin` | Sanitised job view exposing only the `llm_input` feature payload |
| `GET /v1/dashboard/admin/tenants` | `dashboard:admin` | 24h volume and failure rate by tenant |

*Bank tenants* request OAuth tokens with `scope=dashboard:read underwrite:read` to see raw input and LLM output for their own jobs.

*Service provider operators* request tokens with `scope=dashboard:admin` and only see the intermediate `llm_input`, preventing exposure of bank-supplied PII.

Audit records are included with every job detail response so banks can self-serve compliance reviews.

## Next steps

* Configure Alertmanager receivers for incident routing.
* Upload Grafana dashboards to a managed org and provision per-tenant API keys if banks need read-only Grafana access.
* If hosting Prometheus centrally, adjust scrape targets (or use remote write) so bank-specific deployments push metrics without direct networking back to the control plane.
