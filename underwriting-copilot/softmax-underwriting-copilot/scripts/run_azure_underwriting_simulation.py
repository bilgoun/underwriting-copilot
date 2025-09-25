#!/usr/bin/env python3
"""Simulate full underwriting payload and send to Azure GPT."""
from __future__ import annotations

import json
import os
from pathlib import Path
from statistics import mean
from typing import Any, Dict

from openai import AzureOpenAI

from app.pipeline import market_search, parser_adapter, sanitizer

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT.parent / ".env"


def load_env() -> None:
    if not ENV_PATH.exists():
        raise FileNotFoundError(f".env not found at {ENV_PATH}")
    with ENV_PATH.open() as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key, value)


def parse_bank_statement(pdf: Path) -> Dict[str, Any]:
    parsed = parser_adapter.parse(str(pdf))
    rows = parsed.get("rows", [])
    credits = []
    for row in rows:
        if len(row) > 5:
            try:
                credits.append(float(str(row[5]).replace(",", "").strip()))
            except (TypeError, ValueError):
                continue
    avg_income = mean(credits) if credits else 0.0

    def _serialize_row(row: list[Any]) -> list[Any]:
        serialized = []
        for value in row:
            if hasattr(value, "isoformat"):
                try:
                    serialized.append(value.isoformat())
                    continue
                except Exception:  # pragma: no cover - defensive
                    pass
            serialized.append(value)
        return serialized

    return {
        "customer_name": parsed.get("customer_name"),
        "account_number": parsed.get("account_number"),
        "bank_code": parsed.get("bank_code"),
        "average_monthly_income": avg_income,
        "transaction_count": len(rows),
        "period": parsed.get("stats", {}),
        "sample_rows": [_serialize_row(row) for row in rows[:10]],
    }


def load_json(path: Path) -> Dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def build_payload() -> Dict[str, Any]:
    bank_summary = parse_bank_statement(ROOT / "mockdata" / "556468.pdf")
    social_data = load_json(ROOT / "mockdata" / "SocialInsurancemock.json")
    credit_data = load_json(ROOT / "mockdata" / "Creditbureaumock.json")

    social_entries = social_data.get("response", {}).get("listData", [])
    social_salaries = [entry.get("salary") for entry in social_entries if isinstance(entry.get("salary"), (int, float))]
    social_avg_salary = mean(social_salaries) if social_salaries else None

    property_name = "Alpha Zone 3 өрөө 80 мкв"
    market = market_search.gather_market_listings(property_name, 80)

    return {
        "loan_request": {
            "amount_mnt": 50_000_000,
            "purpose": "consumer_loan",
        },
        "bank_statement_summary": bank_summary,
        "credit_bureau_raw": credit_data,
        "social_insurance_raw": social_data,
        "social_average_salary": social_avg_salary,
        "collateral": {
            "name": property_name,
            "market_search": market,
        },
    }


def call_azure(payload: Dict[str, Any]) -> AzureOpenAI:
    developer_prompt = (
        "Та банкны ахлах зээлийн шинжээч. Доорх JSON өгөгдлөөр шийдвэр гаргалтад туустлах "
        "богино, тодорхой, хариуцлагатай кредит мемо (Markdown) бич. Барьцаа хөрөнгийн "
        "веб хайлтын үр дүнг ашиглан эхлээд квадрат метрийн дундаж үнийг тооцоолж, түүнийгээ "
        "тодорхой тайлагна. Дараа нь тухайн үл хөдлөхийн нийт үнийг гарган дүгнэлтдээ тусга."
    )

    client = AzureOpenAI(
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        azure_endpoint=os.environ["AZURE_OPENAI_BASE_URL"],
        api_version="2025-01-01-preview",
    )

    messages = [
        {"role": "developer", "content": [{"type": "text", "text": developer_prompt}]},
        {"role": "user", "content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False)}]},
    ]

    completion = client.chat.completions.create(
        model=os.environ["AZURE_OPENAI_DEPLOYMENT"],
        messages=messages,
        response_format={"type": "text"},
        max_completion_tokens=20_000,
    )

    return completion


def main() -> None:
    load_env()
    payload = build_payload()
    sanitized_payload = sanitizer.sanitize_for_llm(payload)
    print("=== Payload being sent to GPT-5-mini (PII sanitized) ===")
    print(json.dumps(sanitized_payload, ensure_ascii=False, indent=2))

    try:
        completion = call_azure(sanitized_payload)
    except Exception as exc:  # pragma: no cover - network failure paths
        print("\nAzure OpenAI call failed:", exc)
        return

    print("\n=== GPT-5-mini response ===\n")
    print(completion.choices[0].message.content or "<empty response>")
    print("\n=== Token usage ===")
    print(completion.usage)


if __name__ == "__main__":
    main()
