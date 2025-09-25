from __future__ import annotations

import datetime as dt
import uuid
from enum import Enum
from typing import Any, Optional

from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.types import LargeBinary, TypeDecorator

from .utils.crypto import decrypt_json, encrypt_json


def _uuid(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:18]}"


class Base(DeclarativeBase):
    pass


class JobStatus(str, Enum):
    queued = "queued"
    processing = "processing"
    succeeded = "succeeded"
    failed = "failed"


class EncryptedJSON(TypeDecorator[Any]):
    impl = LargeBinary
    cache_ok = True

    def process_bind_param(self, value: Any, dialect) -> Optional[bytes]:  # type: ignore[override]
        if value is None:
            return None
        return encrypt_json(value)

    def process_result_value(self, value: Optional[bytes], dialect) -> Any:  # type: ignore[override]
        if value is None:
            return None
        return decrypt_json(value)


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: _uuid("tenant"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    api_key_hash: Mapped[Optional[str]] = mapped_column(String(128), unique=True)
    oauth_client_id: Mapped[Optional[str]] = mapped_column(String(128), unique=True)
    oauth_client_secret: Mapped[Optional[str]] = mapped_column(String(256))
    tenant_secret: Mapped[str] = mapped_column(String(128), nullable=False)
    webhook_secret: Mapped[str] = mapped_column(String(128), nullable=False)
    rate_limit_cfg: Mapped[dict[str, Any]] = mapped_column(EncryptedJSON, default=dict)
    rate_limit_rps: Mapped[int] = mapped_column(Integer, default=10)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=func.now())

    jobs: Mapped[list["Job"]] = relationship(back_populates="tenant")


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        UniqueConstraint("tenant_id", "client_job_id", name="uq_jobs_tenant_client"),
        Index("ix_jobs_idempotency_key", "idempotency_key"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: _uuid("uwo"))
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    client_job_id: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(SAEnum(JobStatus), default=JobStatus.queued, nullable=False)
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    callback_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    request_hash: Mapped[Optional[str]] = mapped_column(String(64))
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    tenant: Mapped["Tenant"] = relationship(back_populates="jobs")
    payload: Mapped[Optional["Payload"]] = relationship(back_populates="job", uselist=False)
    features: Mapped[Optional["Features"]] = relationship(back_populates="job", uselist=False)
    result: Mapped[Optional["Result"]] = relationship(back_populates="job", uselist=False)
    audits: Mapped[list["Audit"]] = relationship(back_populates="job")


class Payload(Base):
    __tablename__ = "payloads"

    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("jobs.id", ondelete="CASCADE"), primary_key=True
    )
    json_encrypted: Mapped[Optional[dict[str, Any]]] = mapped_column(EncryptedJSON, nullable=True)

    job: Mapped["Job"] = relationship(back_populates="payload")


class Features(Base):
    __tablename__ = "features"

    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("jobs.id", ondelete="CASCADE"), primary_key=True
    )
    json_encrypted: Mapped[Optional[dict[str, Any]]] = mapped_column(EncryptedJSON, nullable=True)

    job: Mapped["Job"] = relationship(back_populates="features")


class Result(Base):
    __tablename__ = "results"

    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("jobs.id", ondelete="CASCADE"), primary_key=True
    )
    memo_markdown: Mapped[Optional[str]] = mapped_column(Text)
    memo_pdf_url: Mapped[Optional[str]] = mapped_column(String(1024))
    risk_score: Mapped[Optional[float]] = mapped_column()
    decision: Mapped[Optional[str]] = mapped_column(String(32))
    interest_rate_suggestion: Mapped[Optional[float]] = mapped_column()
    json_tail: Mapped[Optional[dict[str, Any]]] = mapped_column(EncryptedJSON)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=func.now())

    job: Mapped["Job"] = relationship(back_populates="result")


class Audit(Base):
    __tablename__ = "audits"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: _uuid("audit"))
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"))
    actor: Mapped[str] = mapped_column(String(128))
    action: Mapped[str] = mapped_column(String(128))
    hash: Mapped[Optional[str]] = mapped_column(String(128))
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=func.now())

    job: Mapped["Job"] = relationship(back_populates="audits")
