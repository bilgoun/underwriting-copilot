#!/usr/bin/env python
"""Simple load generator for the underwriting API sandbox."""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import time
from pathlib import Path
from typing import Any, Dict

import httpx

from app.security import sign_payload

FIXTURES = Path(__file__).resolve().parents[1] / "tests" / "fixtures"


def load_payload() -> Dict[str, Any]:
    return json.loads((FIXTURES / "payload.json").read_text())


async def submit_job(
    client: httpx.AsyncClient,
    url: str,
    payload: Dict[str, Any],
    api_key: str,
    tenant_secret: str,
) -> float:
    body = json.dumps(payload, ensure_ascii=False).encode()
    headers = {
        "Content-Type": "application/json",
        "X-Api-Key": api_key,
        "X-Signature": sign_payload(body, tenant_secret),
    }
    start = time.perf_counter()
    response = await client.post(url, content=body, headers=headers)
    response.raise_for_status()
    return time.perf_counter() - start


async def main() -> None:
    parser = argparse.ArgumentParser(description="Softmax underwriting load test")
    parser.add_argument("--api", default="http://localhost:8080/v1/underwrite")
    parser.add_argument("--jobs", type=int, default=100)
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--tenant-secret", required=True)
    parser.add_argument("--tenant-id", required=False, default="tenant")
    args = parser.parse_args()

    payload_template = load_payload()

    async with httpx.AsyncClient(timeout=30) as client:
        durations = []
        for i in range(args.jobs):
            payload = json.loads(json.dumps(payload_template))
            payload["job_id"] = f"load-{i}"
            payload["tenant_id"] = args.tenant_id
            duration = await submit_job(client, args.api, payload, args.api_key, args.tenant_secret)
            durations.append(duration)

    p95 = statistics.quantiles(durations, n=100, method="inclusive")[94] if len(durations) >= 20 else max(durations)
    print(f"Jobs sent: {len(durations)}")
    print(f"p95 latency: {p95:.2f}s")


if __name__ == "__main__":
    asyncio.run(main())
