#!/usr/bin/env python3
"""Simulate underwriting payload and send to Gemini."""
from __future__ import annotations

import json
import os
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List

import requests

from app.pipeline import market_search, parser_adapter, sanitizer

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT.parent / ".env"
GEMINI_MODEL = "gemini-2.5-pro-preview-05-06"


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


def _serialize_row(row: List[Any]) -> List[Any]:
    serialized: List[Any] = []
    for value in row:
        if hasattr(value, "isoformat"):
            try:
                serialized.append(value.isoformat())
                continue
            except Exception:  # pragma: no cover - defensive
                pass
        serialized.append(value)
    return serialized


def parse_bank_statement(pdf: Path) -> Dict[str, Any]:
    parsed = parser_adapter.parse(str(pdf))
    rows = parsed.get("rows", [])
    credits: List[float] = []
    for row in rows:
        if len(row) > 5:
            try:
                credits.append(float(str(row[5]).replace(",", "").strip()))
            except (TypeError, ValueError):
                continue
    avg_income = mean(credits) if credits else 0.0
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


def call_gemini(system_prompt: str, user_payload: Dict[str, Any]) -> Dict[str, Any]:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY missing in environment")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": json.dumps(user_payload, ensure_ascii=False)}],
            }
        ],
        "systemInstruction": {"parts": [{"text": system_prompt}]},
    }

    response = requests.post(url, headers=headers, json=data, timeout=60)
    if response.status_code != 200:
        raise RuntimeError(
            f"Gemini request failed: {response.status_code} — {response.text[:500]}"
        )
    return response.json()


SYSTEM_PROMPT = (
    "Та банкны ахлах зээлийн шинжээч. Доорх JSON өгөгдлөөр шийдвэр гаргалтад туустлах "
    "богино, тодорхой, хариуцлагатай кредит мемо (Markdown) бич. Барьцаа хөрөнгийн "
    "веб хайлтын үр дүнг ашиглан эхлээд квадрат метрийн дундаж үнийг тооцоолж, түүнийгээ "
    "тодорхой тайлагна. Дараа нь тухайн үл хөдлөхийн нийт үнийг гарган дүгнэлтдээ тусга."
)


def extract_gemini_text(result: Dict[str, Any]) -> str:
    try:
        candidates = result.get("candidates", [])
        if not candidates:
            return ""
        content = candidates[0].get("content", {})
        parts = content.get("parts", [])
        for part in parts:
            text = part.get("text")
            if text:
                return text
    except Exception:  # pragma: no cover - defensive
        return ""
    return ""


def main() -> None:
    load_env()
    payload = build_payload()
    sanitized_payload = sanitizer.sanitize_for_llm(payload)
    print("=== Payload sent to Gemini (PII sanitized) ===")
    print(json.dumps(sanitized_payload, ensure_ascii=False, indent=2))

    try:
        result = call_gemini(SYSTEM_PROMPT, sanitized_payload)
    except Exception as exc:
        print("\nGemini API call failed:", exc)
        return

    print("\n=== Raw Gemini response ===")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    analysis = extract_gemini_text(result)
    print("\n=== Gemini analysis text ===\n")
    print(analysis if analysis else "<empty response>")


if __name__ == "__main__":
    main()
