#!/usr/bin/env python
"""Run underwriting simulations for local mock applicants."""

from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import quote_plus

import requests

import sys

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))


def _load_env_files() -> None:
    candidate_paths = [BASE_DIR / ".env", BASE_DIR.parent / ".env"]
    for env_path in candidate_paths:
        if not env_path.exists():
            continue
        for line in env_path.read_text().splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


_load_env_files()

from app.pipeline import llm, parser_adapter
MOCK_DIR = BASE_DIR / "mockdata"
OUTPUT_PATH = BASE_DIR / "simulation_results.json"

SERP_API_KEY = os.getenv("SERPAPI_API_KEY")
COLLATERAL_BASE_URL = os.getenv("SOFTMAX_COLLATERAL_URL", "https://softmax.mn")
COLLATERAL_API_KEY = os.getenv("COLLATERAL_API_KEY") or os.getenv("X_API_KEY")

PDF_MAP: Dict[str, str] = {
    "LoanApplicant_001.json": "20230322-0622.pdf",
    "LoanApplicant_002.json": "425590.pdf",
    "LoanApplicant_003.json": "535971.pdf",
    "LoanApplicant_004.json": "556468.pdf",
}

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


def _coerce_float(value: Any) -> Optional[float]:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        normalized = value.replace(",", "").replace(" ", "")
        try:
            return float(normalized)
        except ValueError:
            return None
    return None


def _coerce_datetime(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(value[: len(fmt)], fmt)
            except ValueError:
                continue
    return None


def compute_bank_summary(applicant_file: str) -> Optional[Dict[str, Any]]:
    pdf_name = PDF_MAP.get(applicant_file)
    if not pdf_name:
        return None

    pdf_path = MOCK_DIR / pdf_name
    if not pdf_path.exists():
        return None

    parse_result = parser_adapter.parse(str(pdf_path))
    rows: Iterable[List[Any]] = parse_result.get("rows", [])

    monthly_totals: Dict[str, float] = defaultdict(float)
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None

    for row in rows:
        if len(row) <= 4:
            continue
        amount = _coerce_float(row[4])
        if amount is None or amount <= 0:
            continue
        date_obj = _coerce_datetime(row[0])
        if not date_obj:
            continue

        key = date_obj.strftime("%Y-%m")
        monthly_totals[key] += amount

        if period_start is None or date_obj < period_start:
            period_start = date_obj
        if period_end is None or date_obj > period_end:
            period_end = date_obj

    if not monthly_totals:
        return None

    avg_income = mean(monthly_totals.values())
    span: Optional[str] = None
    if period_start and period_end:
        span = f"{period_start.strftime('%Y-%m')} to {period_end.strftime('%Y-%m')}"

    return {
        "average_monthly_income_mnt": round(avg_income, 2),
        "statement_period": span,
    }


def fetch_web_search_raw(query: str) -> Dict[str, Any]:
    if SERP_API_KEY:
        params = {
            "engine": "google",
            "api_key": SERP_API_KEY,
            "q": query,
            "hl": "mn",
            "gl": "mn",
            "num": 10,
        }
        response = requests.get("https://serpapi.com/search.json", params=params, timeout=20)
        response.raise_for_status()
        data = response.json()
        lines: List[str] = []
        for item in data.get("organic_results", [])[:10]:
            title = item.get("title")
            snippet = item.get("snippet")
            price = item.get("rich_snippet") or item.get("price")
            parts = [part for part in [title, snippet, price] if part]
            if parts:
                lines.append(" | ".join(str(part) for part in parts))
        raw_text = "\n".join(lines)
        return {
            "engine": "serpapi_google",
            "query": query,
            "requested_url": response.url,
            "raw_response": response.text,
            "raw_text": raw_text,
        }

    url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
    response = requests.get(url, timeout=20, headers={"User-Agent": USER_AGENT})
    response.raise_for_status()
    return {
        "engine": "duckduckgo",
        "query": query,
        "requested_url": url,
        "raw_response": response.text,
        "raw_text": response.text,
    }


def call_vehicle_price_model(collateral: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    payload = {
        "brand": collateral.get("brand", ""),
        "model": collateral.get("model", ""),
        "year_made": collateral.get("year_made") or collateral.get("yearMade", 0),
        "imported_year": collateral.get("imported_year") or collateral.get("importedYear") or collateral.get("year_made") or collateral.get("yearMade", 0),
        "odometer": collateral.get("odometer", 0),
        "hurd": collateral.get("hurd", ""),
        "Хурдны хайрцаг": collateral.get("Хурдны хайрцаг", ""),
        "Хөдөлгүүр": collateral.get("Хөдөлгүүр", ""),
        "Өнгө": collateral.get("Өнгө", ""),
    }

    headers = {"Content-Type": "application/json"}
    if COLLATERAL_API_KEY:
        headers["X-API-KEY"] = COLLATERAL_API_KEY

    url = f"{COLLATERAL_BASE_URL.rstrip('/')}/api/predict-price/"
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=20)
        response.raise_for_status()
    except requests.RequestException as exc:  # pragma: no cover - network
        return {
            "request_payload": payload,
            "error": str(exc),
        }

    raw_text = response.text
    try:
        data = response.json()
    except ValueError:
        data = None

    predicted = None
    if isinstance(data, dict):
        predicted = data.get("predicted_price")

    return {
        "request_payload": payload,
        "response_raw": raw_text,
        "response_json": data,
        "predicted_price": predicted,
    }


def build_collateral_section(collaterals: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    primary: Optional[Dict[str, Any]] = None

    for collateral in collaterals:
        collateral_type = str(collateral.get("type", "")).lower()
        if collateral_type == "vehicle":
            brand = collateral.get("brand", "")
            model = collateral.get("model", "")
            year = collateral.get("year_made") or collateral.get("yearMade") or ""
            query = " ".join(filter(None, [brand, model, str(year), "зарна", "үнэ"]))
            ml_payload = call_vehicle_price_model(collateral)
        elif collateral_type in {"real estate", "property", "apartment", "house"}:
            address = collateral.get("address") or collateral.get("name") or ""
            query = " ".join(filter(None, [address, "зарна", "үнэ"]))
            ml_payload = None
        else:
            query = None
            ml_payload = None

        search_payload: Optional[Dict[str, Any]] = None
        if query:
            try:
                search_payload = fetch_web_search_raw(query)
            except requests.RequestException as exc:  # pragma: no cover - network
                search_payload = {
                    "engine": "google",
                    "query": query,
                    "error": str(exc),
                }

        predicted_value = None
        raw_ml = None
        ml_json = None
        if ml_payload:
            predicted_value = ml_payload.get("predicted_price")
            raw_ml = ml_payload.get("response_raw")
            ml_json = ml_payload.get("response_json")

        entry = {
            "original_payload": collateral,
            "search_query": query,
            "web_search_results": [search_payload] if search_payload else [],
            "ml_response_raw": raw_ml,
            "ml_response_json": ml_json,
            "predicted_value_mnt": predicted_value,
            "ml_error": ml_payload.get("error") if isinstance(ml_payload, dict) else None,
        }
        if primary is None:
            primary = entry

    return primary


def collect_applicant_files(filter_token: Optional[str] = None) -> List[Path]:
    candidates = sorted(MOCK_DIR.glob("LoanApplicant_*.json"))
    if filter_token:
        candidates = [path for path in candidates if filter_token in path.name]
    return candidates


def build_simulation_payload(applicant_path: Path) -> Dict[str, Any]:
    raw_data = json.loads(applicant_path.read_text())

    credit_keys = ["bureau", "pull", "summary", "accounts", "inquiries"]
    credit_data = {key: raw_data.get(key) for key in credit_keys if key in raw_data}
    social_data = raw_data.get("response")
    collateral_offered = raw_data.get("collateralOffered") or []
    loan_request = raw_data.get("requestedLoan") or {}

    bank_summary = compute_bank_summary(applicant_path.name)
    primary_collateral = build_collateral_section(collateral_offered)

    documents: Dict[str, Any] = {}
    pdf_name = PDF_MAP.get(applicant_path.name)
    if pdf_name:
        documents["bank_statement_url"] = f"https://example.com/{pdf_name}"

    raw_input: Dict[str, Any] = {
        "credit_bureau_data": credit_data,
        "collateral_offered": collateral_offered,
        "loan_request": loan_request,
    }
    if social_data:
        raw_input["social_insurance_data"] = social_data
    if documents:
        raw_input["documents"] = documents

    llm_input: Dict[str, Any] = {
        "credit_bureau_data": credit_data,
        "loan_request": loan_request,
    }
    if social_data:
        llm_input["social_insurance_data"] = social_data
    if bank_summary:
        llm_input["bank_statement"] = bank_summary
    if primary_collateral:
        primary_clone = json.loads(json.dumps(primary_collateral, ensure_ascii=False))
        for result in primary_clone.get("web_search_results", []) or []:
            raw_response = result.get("raw_response")
            if isinstance(raw_response, str) and len(raw_response) > 5000:
                result["raw_response"] = raw_response[:5000]
            raw_text = result.get("raw_text")
            if isinstance(raw_text, str) and len(raw_text) > 5000:
                result["raw_text"] = raw_text[:5000]
        raw_ml = primary_clone.get("ml_response_raw")
        if isinstance(raw_ml, str) and len(raw_ml) > 5000:
            primary_clone["ml_response_raw"] = raw_ml[:5000]
        llm_input["collateral"] = primary_clone

    llm_output: Dict[str, Any]
    try:
        memo, _ = llm.generate_memo(llm_input)
        llm_output = {"memo": memo}
    except Exception as exc:
        llm_output = {
            "error": str(exc),
        }

    return {
        "raw_input": raw_input,
        "llm_input": llm_input,
        "llm_output": llm_output,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Underwriting simulation runner")
    parser.add_argument("--app", dest="app_filter", help="Process only applicants containing this token", default=None)
    args = parser.parse_args()

    results: List[Dict[str, Any]] = []
    for applicant_file in collect_applicant_files(args.app_filter):
        simulation = build_simulation_payload(applicant_file)
        results.append(simulation)

    OUTPUT_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
