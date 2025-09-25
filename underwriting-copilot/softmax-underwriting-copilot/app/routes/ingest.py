from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from .. import metrics
from ..db import (
    append_audit,
    create_job,
    get_job_by_idempotency,
    get_job_by_request_hash,
    get_session,
    get_tenant_by_id,
    hash_body,
    hash_header,
)
from ..schemas import CanonicalPayload, UnderwriteAcceptedResponse
from ..security import TenantAuthContext, enforce_rate_limit, verify_inbound_signature
from ..workers.tasks import enqueue_underwrite_job

router = APIRouter(prefix="/v1", tags=["underwriting"])

IDEMPOTENCY_HEADER = "Idempotency-Key"


@router.post(
    "/underwrite",
    response_model=UnderwriteAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def submit_underwriting_job(
    request: Request,
    payload: CanonicalPayload,
    session: Session = Depends(get_session),
    auth_ctx: TenantAuthContext = Depends(verify_inbound_signature),
    _: TenantAuthContext = Depends(enforce_rate_limit),
) -> UnderwriteAcceptedResponse:
    raw_body = getattr(request.state, "raw_body", None)
    if raw_body is None:
        raw_body = payload.model_dump_json(by_alias=True, exclude_none=True).encode()

    idempotency_key = request.headers.get(IDEMPOTENCY_HEADER)
    idempotency_hash = hash_header(idempotency_key)
    request_hash = hash_body(raw_body)

    if idempotency_hash:
        existing = get_job_by_idempotency(session, auth_ctx.tenant_id, idempotency_hash)
        if existing:
            return UnderwriteAcceptedResponse(job_id=existing.id, status=existing.status.value)

    duplicate = get_job_by_request_hash(session, auth_ctx.tenant_id, request_hash)
    if duplicate:
        return UnderwriteAcceptedResponse(job_id=duplicate.id, status=duplicate.status.value)

    tenant = get_tenant_by_id(session, auth_ctx.tenant_id)
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Tenant missing")

    job_payload = payload.model_dump(by_alias=True, exclude_none=True)
    job = create_job(
        session=session,
        tenant=tenant,
        payload=job_payload,
        idempotency_hash=idempotency_hash,
        request_hash=request_hash,
        callback_url=str(payload.callback_url),
    )
    append_audit(session, job, actor="api", action="job_queued", hash_value=request_hash)

    metrics.jobs_created_total.labels(tenant_id=tenant.id).inc()
    enqueue_underwrite_job(job.id)

    return UnderwriteAcceptedResponse(job_id=job.id, status=job.status.value)
