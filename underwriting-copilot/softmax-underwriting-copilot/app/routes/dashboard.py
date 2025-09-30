from __future__ import annotations

import datetime as dt
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..db import (
    get_job_with_details,
    get_session,
    list_jobs_for_tenant,
    list_recent_jobs,
    list_tenants,
    tenant_job_stats,
)
from ..models import Job, JobStatus
from ..schemas import (
    AdminTenantOverviewResponse,
    DashboardJobDetail,
    DashboardJobSummary,
    DashboardJobsResponse,
    DashboardSummary,
    TenantDashboardSummaryResponse,
    TenantOverview,
)
from ..security import TenantAuthContext, require_scopes

router = APIRouter(prefix="/v1/dashboard", tags=["dashboard"])


def _processing_seconds(job: Job) -> Optional[float]:
    if job.created_at and job.updated_at:
        return (job.updated_at - job.created_at).total_seconds()
    return None


def _job_to_summary(job: Job) -> DashboardJobSummary:
    result = job.result
    return DashboardJobSummary(
        job_id=job.id,
        tenant_id=job.tenant_id,
        client_job_id=job.client_job_id,
        status=job.status.value if isinstance(job.status, JobStatus) else str(job.status),
        decision=result.decision if result else None,
        risk_score=result.risk_score if result else None,
        created_at=job.created_at,
        updated_at=job.updated_at,
        processing_seconds=_processing_seconds(job),
    )


def _summaries_to_overview(summaries: List[DashboardJobSummary]) -> DashboardSummary:
    total = len(summaries)
    succeeded = sum(1 for summary in summaries if summary.status == JobStatus.succeeded.value)
    failed = sum(1 for summary in summaries if summary.status == JobStatus.failed.value)
    durations = [s.processing_seconds for s in summaries if s.processing_seconds is not None]
    average = (sum(durations) / len(durations)) if durations else None
    return DashboardSummary(
        total_jobs=total,
        succeeded_jobs=succeeded,
        failed_jobs=failed,
        average_processing_seconds=average,
    )


def _job_to_detail(
    job: Job,
    *,
    include_raw_input: bool,
    include_llm_input: bool,
    include_llm_output: bool,
) -> DashboardJobDetail:
    summary = _job_to_summary(job)
    payload = job.payload.json_encrypted if (include_raw_input and job.payload) else None
    features = job.features.json_encrypted if (include_llm_input and job.features) else None
    result = job.result
    audits = [
        {
            "id": audit.id,
            "actor": audit.actor,
            "action": audit.action,
            "created_at": audit.created_at,
        }
        for audit in sorted(job.audits, key=lambda record: record.created_at)
    ]
    return DashboardJobDetail(
        summary=summary,
        raw_input=payload,
        llm_input=features,
        llm_output_markdown=result.memo_markdown if include_llm_output and result else None,
        llm_output_metadata=result.json_tail if result else None,
        audits=audits,
    )


def _parse_status(value: Optional[str]) -> Optional[JobStatus]:
    if value is None:
        return None
    try:
        return JobStatus(value)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status filter") from exc


@router.get("/tenant/jobs", response_model=DashboardJobsResponse)
async def list_tenant_jobs(
    *,
    limit: int = Query(20, ge=1, le=200),
    status_filter: Optional[str] = Query(None, alias="status"),
    session: Session = Depends(get_session),
    ctx: TenantAuthContext = Depends(require_scopes("dashboard:read")),
) -> DashboardJobsResponse:
    status_enum = _parse_status(status_filter)
    jobs = list_jobs_for_tenant(session, ctx.tenant_id, limit=limit, status=status_enum)
    summaries = [_job_to_summary(job) for job in jobs]
    return DashboardJobsResponse(summary=_summaries_to_overview(summaries), jobs=summaries)


@router.get("/tenant/jobs/{job_id}", response_model=DashboardJobDetail)
async def tenant_job_detail(
    job_id: str,
    session: Session = Depends(get_session),
    ctx: TenantAuthContext = Depends(require_scopes("dashboard:read")),
) -> DashboardJobDetail:
    job = get_job_with_details(session, job_id)
    if job is None or job.tenant_id != ctx.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    # Banks can see raw_input and llm_output, but NOT llm_input
    return _job_to_detail(job, include_raw_input=True, include_llm_input=False, include_llm_output=True)


@router.get("/tenant/summary", response_model=TenantDashboardSummaryResponse)
async def tenant_summary(
    *,
    lookback_hours: int = Query(24, ge=1, le=168),
    session: Session = Depends(get_session),
    ctx: TenantAuthContext = Depends(require_scopes("dashboard:read")),
) -> TenantDashboardSummaryResponse:
    since = dt.datetime.utcnow() - dt.timedelta(hours=lookback_hours)
    stats = tenant_job_stats(session, since)
    tenant_stats = stats.get(ctx.tenant_id)
    if tenant_stats is None:
        summary = DashboardSummary(total_jobs=0, succeeded_jobs=0, failed_jobs=0, average_processing_seconds=None)
    else:
        summary = DashboardSummary(
            total_jobs=int(tenant_stats["total"]),
            succeeded_jobs=int(tenant_stats["succeeded"]),
            failed_jobs=int(tenant_stats["failed"]),
            average_processing_seconds=tenant_stats["avg_processing"],
        )
    return TenantDashboardSummaryResponse(summary=summary)


@router.get("/admin/tenants", response_model=AdminTenantOverviewResponse)
async def admin_tenant_overview(
    *,
    session: Session = Depends(get_session),
    ctx: TenantAuthContext = Depends(require_scopes("dashboard:admin")),
    lookback_hours: int = Query(24, ge=1, le=720),
) -> AdminTenantOverviewResponse:
    _ = ctx  # prevent unused warning
    since = dt.datetime.utcnow() - dt.timedelta(hours=lookback_hours)
    stats_map = tenant_job_stats(session, since)
    tenants = list_tenants(session)
    overviews: List[TenantOverview] = []
    for tenant in tenants:
        data = stats_map.get(tenant.id, {"total": 0, "failed": 0, "succeeded": 0, "avg_processing": None})
        total_jobs = int(data["total"])
        failed_jobs = int(data["failed"])
        failure_rate = (failed_jobs / total_jobs * 100.0) if total_jobs else 0.0
        overviews.append(
            TenantOverview(
                tenant_id=tenant.id,
                name=tenant.name,
                total_jobs_24h=total_jobs,
                failure_rate_24h=round(failure_rate, 2),
            )
        )
    return AdminTenantOverviewResponse(tenants=overviews)


@router.get("/admin/jobs", response_model=DashboardJobsResponse)
async def admin_jobs(
    *,
    session: Session = Depends(get_session),
    ctx: TenantAuthContext = Depends(require_scopes("dashboard:admin")),
    tenant_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
) -> DashboardJobsResponse:
    _ = ctx
    jobs = list_recent_jobs(session, limit=limit, tenant_id=tenant_id)
    summaries = [_job_to_summary(job) for job in jobs]
    return DashboardJobsResponse(summary=_summaries_to_overview(summaries), jobs=summaries)


@router.get("/admin/jobs/{job_id}", response_model=DashboardJobDetail)
async def admin_job_detail(
    job_id: str,
    session: Session = Depends(get_session),
    ctx: TenantAuthContext = Depends(require_scopes("dashboard:admin")),
) -> DashboardJobDetail:
    _ = ctx
    job = get_job_with_details(session, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    # Admins can see EVERYTHING: raw_input, llm_input, and llm_output
    return _job_to_detail(job, include_raw_input=True, include_llm_input=True, include_llm_output=True)

