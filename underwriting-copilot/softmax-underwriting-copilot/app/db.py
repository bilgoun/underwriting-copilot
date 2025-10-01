from __future__ import annotations

import datetime as dt
import hashlib
from contextlib import contextmanager
from typing import Dict, Generator, Optional

from sqlalchemy import case, create_engine, func, select
from sqlalchemy.pool import StaticPool
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker, selectinload

from .config import get_settings
from .models import Audit, Base, Features, Job, JobStatus, Payload, Result, Tenant

_engine: Optional[Engine] = None
_SessionLocal: Optional[sessionmaker] = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        settings = get_settings()
        connect_args: dict[str, object] = {}
        pool_args = {}
        if settings.database_url.startswith('sqlite'):
            connect_args['check_same_thread'] = False
            if ':memory:' in settings.database_url:
                pool_args['poolclass'] = StaticPool
        _engine = create_engine(settings.database_url, pool_pre_ping=True, future=True, connect_args=connect_args, **pool_args)
    return _engine


def get_session_factory() -> sessionmaker:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            bind=get_engine(),
            autoflush=False,
            autocommit=False,
            future=True,
            expire_on_commit=False,
        )
    return _SessionLocal


def get_session() -> Generator[Session, None, None]:
    session_factory = get_session_factory()
    session = session_factory()
    try:
        yield session
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise
    finally:
        session.close()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    session_factory = get_session_factory()
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    engine = get_engine()
    Base.metadata.create_all(bind=engine)


def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()


def hash_header(value: str | None) -> Optional[str]:
    if not value:
        return None
    return hashlib.sha256(value.encode()).hexdigest()


def hash_body(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()

def hash_secret(secret: str) -> str:
    return hashlib.sha256(secret.encode()).hexdigest()


def get_tenant_by_api_key(session: Session, api_key: str) -> Optional[Tenant]:
    hashed = hash_api_key(api_key)
    return session.execute(select(Tenant).where(Tenant.api_key_hash == hashed)).scalar_one_or_none()

def get_tenant_by_client_credentials(session: Session, client_id: str, client_secret: str) -> Optional[Tenant]:
    hashed = hash_secret(client_secret)
    stmt = select(Tenant).where(Tenant.oauth_client_id == client_id, Tenant.oauth_client_secret == hashed)
    return session.execute(stmt).scalar_one_or_none()


def get_tenant_by_id(session: Session, tenant_id: str | None) -> Optional[Tenant]:
    if tenant_id is None:
        return None
    return session.execute(select(Tenant).where(Tenant.id == tenant_id)).scalar_one_or_none()


def get_job_by_id(session: Session, job_id: str) -> Optional[Job]:
    return session.execute(select(Job).where(Job.id == job_id)).scalar_one_or_none()


def get_job_by_client_id(session: Session, tenant_id: str, client_job_id: str) -> Optional[Job]:
    stmt = select(Job).where(Job.tenant_id == tenant_id, Job.client_job_id == client_job_id)
    return session.execute(stmt).scalar_one_or_none()


def get_job_by_idempotency(session: Session, tenant_id: str, idem_hash: str) -> Optional[Job]:
    stmt = select(Job).where(Job.tenant_id == tenant_id, Job.idempotency_key == idem_hash)
    return session.execute(stmt).scalar_one_or_none()


def get_job_by_request_hash(session: Session, tenant_id: str, request_hash: str) -> Optional[Job]:
    stmt = select(Job).where(Job.tenant_id == tenant_id, Job.request_hash == request_hash)
    return session.execute(stmt).scalar_one_or_none()


def create_job(
    session: Session,
    tenant: Tenant,
    payload: Dict,
    idempotency_hash: Optional[str],
    request_hash: str,
    callback_url: str,
) -> Job:
    job = Job(
        tenant_id=tenant.id,
        client_job_id=payload.get("job_id"),
        idempotency_key=idempotency_hash,
        callback_url=callback_url,
        request_hash=request_hash,
    )
    session.add(job)
    session.flush()

    payload_row = Payload(job_id=job.id)
    payload_row.json_encrypted = payload
    session.add(payload_row)
    session.flush()
    return job


def persist_features(session: Session, job: Job, features: Dict) -> None:
    record = session.get(Features, job.id)
    if not record:
        record = Features(job_id=job.id)
    record.json_encrypted = features
    session.add(record)


def persist_result(
    session: Session,
    job: Job,
    memo_markdown: str,
    memo_pdf_url: Optional[str],
    risk_score: Optional[float],
    decision: Optional[str],
    interest_rate: Optional[float],
    json_tail: Dict,
) -> Result:
    record = session.get(Result, job.id)
    if not record:
        record = Result(job_id=job.id)
    record.memo_markdown = memo_markdown
    record.memo_pdf_url = memo_pdf_url
    record.risk_score = risk_score
    record.decision = decision
    record.interest_rate_suggestion = interest_rate
    record.json_tail = json_tail
    session.add(record)
    return record


def append_audit(session: Session, job: Job, actor: str, action: str, hash_value: Optional[str]) -> Audit:
    audit = Audit(job_id=job.id, actor=actor, action=action, hash=hash_value)
    session.add(audit)
    session.flush()
    return audit


def update_job_status(session: Session, job: Job, status: JobStatus) -> None:
    job.status = status
    session.add(job)


def reserve_next_job(session: Session, tenant_id: str) -> Optional[Job]:
    stmt = (
        select(Job)
        .where(Job.tenant_id == tenant_id, Job.status == JobStatus.queued)
        .order_by(Job.created_at)
        .limit(1)
    )
    job = session.execute(stmt).scalar_one_or_none()
    if job:
        job.status = JobStatus.processing
        session.add(job)
    return job


def list_jobs_for_tenant(
    session: Session,
    tenant_id: str,
    *,
    limit: int = 50,
    offset: int = 0,
    status: Optional[JobStatus] = None,
) -> list[Job]:
    stmt = (
        select(Job)
        .where(Job.tenant_id == tenant_id)
        .order_by(Job.created_at.desc())
        .limit(limit)
        .offset(offset)
        .options(
            selectinload(Job.payload),
            selectinload(Job.result),
            selectinload(Job.features),
            selectinload(Job.audits),
        )
    )
    if status is not None:
        stmt = stmt.where(Job.status == status)
    result = session.execute(stmt)
    return list(result.scalars())


def get_job_with_details(session: Session, job_id: str) -> Optional[Job]:
    stmt = (
        select(Job)
        .where(Job.id == job_id)
        .options(
            selectinload(Job.payload),
            selectinload(Job.result),
            selectinload(Job.features),
            selectinload(Job.audits),
            selectinload(Job.tenant),
        )
    )
    return session.execute(stmt).scalar_one_or_none()


def list_tenants(session: Session) -> list[Tenant]:
    return list(session.execute(select(Tenant)).scalars())


def list_recent_jobs(
    session: Session,
    *,
    limit: int = 50,
    tenant_id: Optional[str] = None,
) -> list[Job]:
    stmt = (
        select(Job)
        .order_by(Job.created_at.desc())
        .limit(limit)
        .options(
            selectinload(Job.payload),
            selectinload(Job.result),
            selectinload(Job.features),
            selectinload(Job.audits),
            selectinload(Job.tenant),
        )
    )
    if tenant_id is not None:
        stmt = stmt.where(Job.tenant_id == tenant_id)
    return list(session.execute(stmt).scalars())


def tenant_job_stats(
    session: Session, since: Optional[dt.datetime] = None
) -> dict[str, dict[str, float | int | None]]:
    processing_expr = func.extract("epoch", Job.updated_at - Job.created_at)
    stmt = select(
        Job.tenant_id,
        func.count().label("total"),
        func.sum(case((Job.status == JobStatus.failed, 1), else_=0)).label("failed"),
        func.sum(case((Job.status == JobStatus.succeeded, 1), else_=0)).label("succeeded"),
        func.avg(case((Job.status == JobStatus.succeeded, processing_expr), else_=None)).label(
            "avg_processing"
        ),
    )
    if since is not None:
        stmt = stmt.where(Job.created_at >= since)
    stmt = stmt.group_by(Job.tenant_id)

    stats: dict[str, dict[str, Optional[float]]] = {}
    for row in session.execute(stmt):
        stats[row.tenant_id] = {
            "total": int(row.total or 0),
            "failed": int(row.failed or 0),
            "succeeded": int(row.succeeded or 0),
            "avg_processing": float(row.avg_processing) if row.avg_processing is not None else None,
        }
    return stats
