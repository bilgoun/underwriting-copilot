from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any, Dict

import structlog
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from .. import metrics
from ..metrics import underwrite_duration_seconds
from ..db import (
    append_audit,
    get_job_by_id,
    persist_features,
    persist_result,
    session_scope,
    update_job_status,
)
from ..models import JobStatus
from ..pipeline import collateral, fuse, llm, parser_adapter
from ..security import sign_json
from ..utils import pdf, storage, webhooks
from .celery_app import celery_app

logger = structlog.get_logger("workers.tasks")
tracer = trace.get_tracer("app.workers.tasks")


@celery_app.task(name="app.workers.tasks.underwrite")
def underwrite(job_id: str) -> None:
    with tracer.start_as_current_span("underwrite.job", attributes={"job.id": job_id}) as span:
        with session_scope() as session:
            job = get_job_by_id(session, job_id)
            if job is None:
                span.set_status(Status(StatusCode.ERROR, "job_missing"))
                logger.warning("job_missing", job_id=job_id)
                return

            tenant_id = job.tenant_id
            span.set_attribute("tenant.id", tenant_id)
            update_job_status(session, job, JobStatus.processing)

            payload_row = job.payload
            if payload_row is None or payload_row.json_encrypted is None:
                span.set_status(Status(StatusCode.ERROR, "payload_missing"))
                logger.error("payload_missing", job_id=job.id)
                update_job_status(session, job, JobStatus.failed)
                metrics.jobs_failed_total.labels(tenant_id=tenant_id).inc()
                return

            payload_data: Dict[str, Any] = payload_row.json_encrypted
            tmp_path: Path | None = None
            try:
                with metrics.latency_timer(underwrite_duration_seconds, tenant_id=tenant_id, stage="total"):
                    # Try to process bank statement if provided, but continue without it if unavailable
                    parse_out: Dict[str, Any] = {}
                    bank_statement_url = payload_data.get("documents", {}).get("bank_statement_url")

                    if bank_statement_url and bank_statement_url != "null":
                        with tracer.start_as_current_span(
                            "underwrite.parse_bank_statement",
                            attributes={"job.id": job.id, "tenant.id": tenant_id},
                        ):
                            try:
                                tmp_path = storage.download_to_tmp(bank_statement_url)
                                pdf.validate_pdf(tmp_path)
                                with metrics.latency_timer(metrics.parser_seconds, tenant_id=tenant_id):
                                    parse_out = parser_adapter.parse(str(tmp_path))
                                logger.info("bank_statement_processed", job_id=job.id)
                            except Exception as exc:
                                trace.get_current_span().record_exception(exc)
                                logger.warning("bank_statement_unavailable", job_id=job.id, error=str(exc))
                                parse_out = {}  # Empty - don't include in LLM input
                    else:
                        logger.info("no_bank_statement_provided", job_id=job.id)
                        parse_out = {}  # Empty - don't include in LLM input

                    with tracer.start_as_current_span(
                        "underwrite.collateral_enrichment",
                        attributes={"tenant.id": tenant_id, "job.id": job.id},
                    ):
                        with metrics.latency_timer(metrics.collateral_seconds, tenant_id=tenant_id):
                            collateral_out = collateral.valuate_collateral(payload_data)

                    with tracer.start_as_current_span(
                        "underwrite.feature_fusion",
                        attributes={"tenant.id": tenant_id, "job.id": job.id},
                    ):
                        features = fuse.fuse_features(payload_data, parse_out, collateral_out)
                        persist_features(session, job, features)

                    with tracer.start_as_current_span(
                        "underwrite.generate_memo",
                        attributes={"tenant.id": tenant_id, "job.id": job.id},
                    ):
                        with metrics.latency_timer(metrics.llm_seconds, tenant_id=tenant_id):
                            memo_markdown, meta = llm.generate_memo(features)

                    decision = meta.get("decision")
                    interest = meta.get("interest_rate_suggestion")
                    risk_score = meta.get("risk_score")
                json_tail = {
                    "parser": parse_out,
                    "collateral": collateral_out,
                    "llm_raw_response": meta.get("raw_response"),
                }
                persist_result(
                    session,
                    job,
                    memo_markdown=memo_markdown,
                    memo_pdf_url=None,
                    risk_score=risk_score,
                    decision=decision,
                    interest_rate=interest,
                    json_tail=json_tail,
                )

                update_job_status(session, job, JobStatus.succeeded)
                audit = append_audit(
                    session,
                    job,
                    actor="underwrite_worker",
                    action="job_completed",
                    hash_value=None,
                )

                webhook_payload = {
                    "event": "memo.generated",
                    "job_id": job.id,
                    "client_job_id": job.client_job_id,
                    "decision": decision,
                    "interest_rate_suggestion": interest,
                    "risk_score": risk_score,
                    "llm_input": features,
                    "credit_memo_markdown": memo_markdown,
                    "attachments": [
                        {"type": "json", "name": "features.json", "url": "https://example.com/features"}
                    ],
                    "audit_ref": audit.id,
                    "timestamp": dt.datetime.utcnow().isoformat() + "Z",
                }
                webhook_payload["signature"] = sign_json(webhook_payload, job.tenant.webhook_secret)
                try:
                    webhooks.emit(job.callback_url, webhook_payload, job.tenant.webhook_secret)
                    metrics.webhook_attempts_total.labels(tenant_id=tenant_id, status="success").inc()
                except Exception as exc:  # pragma: no cover
                    trace.get_current_span().record_exception(exc)
                    metrics.webhook_attempts_total.labels(tenant_id=tenant_id, status="error").inc()
                    metrics.webhook_failures_total.labels(tenant_id=tenant_id).inc()
                    logger.warning("webhook_failed", job_id=job.id, error=str(exc))

            except Exception as exc:  # pragma: no cover
                span.record_exception(exc)
                span.set_status(Status(StatusCode.ERROR, str(exc)))
                logger.exception("underwrite_failed", job_id=job.id, error=str(exc))
                update_job_status(session, job, JobStatus.failed)
                metrics.jobs_failed_total.labels(tenant_id=job.tenant_id).inc()
                raise
            finally:
                if tmp_path:
                    storage.cleanup_tmp(tmp_path)


def enqueue_underwrite_job(job_id: str) -> None:
    celery_app.send_task("app.workers.tasks.underwrite", args=[job_id])
