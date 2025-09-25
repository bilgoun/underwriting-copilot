from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..db import (
    append_audit,
    get_job_by_id,
    get_session,
    persist_result,
    reserve_next_job,
    update_job_status,
)
from ..models import JobStatus
from ..schemas import (
    JobResult,
    JobStatusResponse,
    PollingCompleteRequest,
    PollingCompleteResponse,
    PollingPullRequest,
    PollingPullResponse,
)
from ..security import TenantAuthContext, enforce_rate_limit, require_scopes

router = APIRouter(prefix="/v1", tags=["jobs"])


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    session: Session = Depends(get_session),
    ctx: TenantAuthContext = Depends(require_scopes("underwrite:read")),
) -> JobStatusResponse:
    job = get_job_by_id(session, job_id)
    if job is None or job.tenant_id != ctx.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    result = job.result
    metadata = result.json_tail if result and result.json_tail else None
    response = JobResult(
        job_id=job.id,
        status=job.status.value,
        client_job_id=job.client_job_id,
        decision=result.decision if result else None,
        risk_score=result.risk_score if result else None,
        interest_rate_suggestion=result.interest_rate_suggestion if result else None,
        memo_markdown=result.memo_markdown if result else None,
        memo_pdf_url=result.memo_pdf_url if result else None,
        created_at=job.created_at,
        updated_at=job.updated_at,
        metadata=metadata,
    )
    return JobStatusResponse(data=response)


@router.post("/jobs/pull", response_model=PollingPullResponse)
async def polling_pull_jobs(
    request: PollingPullRequest,
    session: Session = Depends(get_session),
    ctx: TenantAuthContext = Depends(require_scopes("underwrite:read")),
    _: TenantAuthContext = Depends(enforce_rate_limit),
) -> PollingPullResponse:
    limit = max(1, min(request.max_jobs, 5))
    jobs = []
    for _ in range(limit):
        job = reserve_next_job(session, ctx.tenant_id)
        if not job:
            break
        payload_row = job.payload
        jobs.append(
            {
                "job_id": job.id,
                "payload": payload_row.json_encrypted if payload_row else {},
            }
        )
    return PollingPullResponse(jobs=jobs)


@router.post("/jobs/complete", response_model=PollingCompleteResponse)
async def polling_complete_job(
    request: PollingCompleteRequest,
    session: Session = Depends(get_session),
    ctx: TenantAuthContext = Depends(require_scopes("underwrite:read")),
) -> PollingCompleteResponse:
    job = get_job_by_id(session, request.job_id)
    if job is None or job.tenant_id != ctx.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    valid_statuses = {s.value for s in JobStatus}
    if request.status not in valid_statuses:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status")

    if request.status == JobStatus.succeeded.value:
        persist_result(
            session,
            job,
            memo_markdown=request.memo_markdown or "",
            memo_pdf_url=None,
            risk_score=request.risk_score,
            decision=request.decision,
            interest_rate=request.interest_rate_suggestion,
            json_tail=request.metadata or {},
        )

    update_job_status(session, job, JobStatus(request.status))
    append_audit(session, job, actor="polling_worker", action="job_complete", hash_value=None)
    return PollingCompleteResponse(job_id=job.id, status=job.status.value)
