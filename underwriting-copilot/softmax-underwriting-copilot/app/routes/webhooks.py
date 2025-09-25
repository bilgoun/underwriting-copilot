from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, status

from ..schemas import WebhookTestRequest
from ..security import TenantAuthContext, enforce_rate_limit, require_scopes, sign_json
from ..utils.webhooks import emit

router = APIRouter(prefix="/v1", tags=["webhooks"])


@router.post("/webhooks/test", status_code=status.HTTP_202_ACCEPTED)
async def send_test_webhook(
    request: WebhookTestRequest,
    ctx: TenantAuthContext = Depends(require_scopes("underwrite:read")),
    _: TenantAuthContext = Depends(enforce_rate_limit),
) -> dict[str, str]:
    payload = {
        "event": "memo.generated",
        "job_id": "uwo_test",
        "client_job_id": "BANK-12345",
        "decision": "REVIEW",
        "interest_rate_suggestion": 18.4,
        "risk_score": 0.43,
        "llm_input": {"example": True},
        "credit_memo_markdown": "## Sample Memo",
        "attachments": [],
        "audit_ref": "audit_test",
        "timestamp": dt.datetime.utcnow().isoformat() + "Z",
    }
    payload["signature"] = sign_json(payload, ctx.webhook_secret)
    emit(request.url, payload, ctx.webhook_secret)
    return {"status": "queued"}
