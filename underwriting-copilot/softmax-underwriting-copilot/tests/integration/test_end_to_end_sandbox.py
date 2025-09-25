from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List

from app.db import create_job, hash_body, session_scope
from app.models import Job, JobStatus
from app.workers.tasks import underwrite

FIXTURES = Path(__file__).parents[1] / "fixtures"


def _load_payload(tenant_id: str) -> Dict:
    data = json.loads((FIXTURES / "payload.json").read_text())
    data["tenant_id"] = tenant_id
    data["documents"]["bank_statement_url"] = "https://storage.test/sample.pdf"
    data["callback_url"] = "https://callback.test/uw"
    return data


def test_end_to_end_underwrite(monkeypatch, tenant):
    payload = _load_payload(tenant.id)

    sample_pdf = FIXTURES / "sample.pdf"

    def fake_download(url: str, suffix: str = ".pdf", timeout: int = 30):
        temp_dir = Path(tempfile.mkdtemp())
        target = temp_dir / "statement.pdf"
        shutil.copy(sample_pdf, target)
        return target

    sent_payloads: List[Dict] = []

    def fake_emit(url: str, payload: Dict, secret: str, timeout: int = 10, max_attempts: int = 3, backoff_seconds: int = 2):
        sent_payloads.append(payload)

    monkeypatch.setattr("app.utils.storage.download_to_tmp", fake_download)
    monkeypatch.setattr("app.utils.webhooks.emit", fake_emit)

    with session_scope() as session:
        job = create_job(
            session,
            tenant,
            payload,
            idempotency_hash=None,
            request_hash=hash_body(json.dumps(payload).encode()),
            callback_url=payload["callback_url"],
        )
        job_id = job.id

    underwrite(job_id)

    with session_scope() as session:
        job = session.get(Job, job_id)
        assert job is not None
        assert job.status == JobStatus.succeeded
        result = job.result
        assert result is not None
        assert result.memo_markdown
        assert result.decision
        assert sent_payloads
        assert sent_payloads[0]["decision"] == result.decision
