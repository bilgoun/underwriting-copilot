from __future__ import annotations

import json
import time
from typing import Any, Dict, List

import requests
import structlog

from ..pipeline import collateral, fuse, llm, parser_adapter
from ..security import sign_payload
from ..utils import pdf, storage

logger = structlog.get_logger("polling_worker")


def _headers(api_key: str, tenant_secret: str, body: Dict[str, Any]) -> Dict[str, str]:
    data = json.dumps(body, ensure_ascii=False).encode()
    signature = sign_payload(data, tenant_secret)
    return {
        "Content-Type": "application/json",
        "X-Api-Key": api_key,
        "X-Signature": signature,
    }


class PollingWorker:
    def __init__(self, base_url: str, api_key: str, tenant_secret: str, interval_seconds: int = 5) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.tenant_secret = tenant_secret
        self.interval_seconds = interval_seconds

    def run_forever(self) -> None:
        while True:
            try:
                jobs = self._pull_jobs()
                for job in jobs:
                    self._process_job(job)
            except Exception as exc:  # pragma: no cover - resilience
                logger.exception("polling_error", error=str(exc))
            time.sleep(self.interval_seconds)

    def _pull_jobs(self) -> List[Dict[str, Any]]:
        body = {"max_jobs": 1}
        response = requests.post(
            f"{self.base_url}/v1/jobs/pull",
            headers=_headers(self.api_key, self.tenant_secret, body),
            json=body,
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        return payload.get("jobs", [])

    def _process_job(self, item: Dict[str, Any]) -> None:
        job_id = item["job_id"]
        payload = item.get("payload", {})
        tmp_path = storage.download_to_tmp(payload["documents"]["bank_statement_url"])
        try:
            pdf.validate_pdf(tmp_path)
            parse_out = parser_adapter.parse(str(tmp_path))
            collateral_out = collateral.valuate_collateral(payload)
            features = fuse.fuse_features(payload, parse_out, collateral_out)
            memo_markdown, meta = llm.generate_memo(features)
            decision = meta.get("decision")
            body = {
                "job_id": job_id,
                "status": "succeeded",
                "decision": decision,
                "interest_rate_suggestion": meta.get("interest_rate_suggestion"),
                "risk_score": meta.get("risk_score"),
                "memo_markdown": memo_markdown,
                "metadata": {
                    "parser": parse_out,
                    "collateral": collateral_out,
                    "llm_raw_response": meta.get("raw_response"),
                },
            }
            response = requests.post(
                f"{self.base_url}/v1/jobs/complete",
                headers=_headers(self.api_key, self.tenant_secret, body),
                json=body,
                timeout=30,
            )
            response.raise_for_status()
            logger.info("job_complete", job_id=job_id)
        finally:
            storage.cleanup_tmp(tmp_path)
