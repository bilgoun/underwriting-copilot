from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import AnyHttpUrl, BaseModel, Field
from pydantic import ConfigDict


class Applicant(BaseModel):
    citizen_id: str
    full_name: str
    phone: str


class Loan(BaseModel):
    type: str
    amount: int
    term_months: int


class StatementPeriod(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    from_: datetime = Field(alias="from")
    to: datetime


class Documents(BaseModel):
    bank_statement_url: AnyHttpUrl
    bank_statement_period: StatementPeriod


class ConsentArtifact(BaseModel):
    provider: str
    reference: str
    scopes: List[str]
    issued_at: datetime
    expires_at: datetime
    hash: str


class CanonicalPayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    job_id: str
    tenant_id: str
    applicant: Applicant
    loan: Loan
    consent_artifact: ConsentArtifact
    third_party_data: Dict[str, Any]
    documents: Documents
    collateral: Dict[str, Any]
    callback_url: AnyHttpUrl


class UnderwriteAcceptedResponse(BaseModel):
    job_id: str
    status: str = "queued"


class JobResult(BaseModel):
    job_id: str
    status: str
    client_job_id: str
    decision: Optional[str] = None
    risk_score: Optional[float] = None
    interest_rate_suggestion: Optional[float] = None
    memo_markdown: Optional[str] = None
    memo_pdf_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    metadata: Optional[Dict[str, Any]] = None


class JobStatusResponse(BaseModel):
    data: JobResult


class OAuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    scope: str


class OAuthTokenRequest(BaseModel):
    grant_type: str
    client_id: str
    client_secret: str
    scope: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "grant_type": "client_credentials",
                "client_id": "tenant_client_id",
                "client_secret": "secret",
                "scope": "underwrite:create underwrite:read",
            }
        }
    }


class WebhookTestRequest(BaseModel):
    url: AnyHttpUrl


class WebhookPayload(BaseModel):
    event: str
    job_id: str
    client_job_id: str
    decision: str
    interest_rate_suggestion: float
    risk_score: float
    llm_input: Dict[str, Any]
    credit_memo_markdown: str
    attachments: List[Dict[str, Any]]
    audit_ref: str
    timestamp: datetime
    signature: str


class PollingPullRequest(BaseModel):
    max_jobs: int = 1


class PollingJobPayload(BaseModel):
    job_id: str
    payload: Dict[str, Any]


class PollingPullResponse(BaseModel):
    jobs: List[PollingJobPayload]


class PollingCompleteRequest(BaseModel):
    job_id: str
    status: str
    decision: Optional[str] = None
    interest_rate_suggestion: Optional[float] = None
    risk_score: Optional[float] = None
    memo_markdown: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class PollingCompleteResponse(BaseModel):
    job_id: str
    status: str
