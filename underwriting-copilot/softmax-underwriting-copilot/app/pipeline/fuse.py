from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, Optional


def fuse_features(
    payload: Dict[str, Any],
    parser_output: Dict[str, Any],
    collateral_output: Dict[str, Any],
) -> Dict[str, Any]:
    """Assemble the exact LLM input structure from upstream payloads and enrichments."""
    third_party = payload.get("third_party_data", {})

    credit_data = _safe_copy(
        third_party.get("mongolbank_credit")
        or payload.get("credit_bureau_data")
    )

    social_block = third_party.get("social_security")
    social_data: Optional[Dict[str, Any]] = None
    if isinstance(social_block, dict):
        candidate = social_block.get("response") or social_block.get("data") or social_block
        if isinstance(candidate, dict):
            social_data = _safe_copy(candidate)
    elif payload.get("social_insurance_data"):
        social_data = _safe_copy(payload.get("social_insurance_data"))

    documents = payload.get("documents") or {}
    bank_summary = _compute_bank_summary(parser_output or {}, documents)

    collateral_section = _build_collateral_section(
        payload.get("collateral") or payload.get("collateral_offered"),
        collateral_output,
    )

    loan_request = _build_loan_request(payload.get("loan") or payload.get("loan_request"))

    llm_input: Dict[str, Any] = {}
    if credit_data:
        llm_input["credit_bureau_data"] = credit_data
    if loan_request:
        llm_input["loan_request"] = loan_request
    if social_data:
        llm_input["social_insurance_data"] = social_data
    if bank_summary:
        llm_input["bank_statement"] = bank_summary
    if collateral_section:
        llm_input["collateral"] = collateral_section

    return llm_input


def _safe_copy(value: Any) -> Any:
    if value is None:
        return None
    return json.loads(json.dumps(value, ensure_ascii=False))


def _build_loan_request(source: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not isinstance(source, dict):
        return None

    mapping = {
        "amountMNT": source.get("amount") or source.get("amountMNT"),
        "termMonths": source.get("term_months") or source.get("termMonths"),
        "aprPct": source.get("aprPct") or source.get("apr_pct"),
        "estimatedMonthlyInstallmentMNT": source.get("estimatedMonthlyInstallmentMNT"),
        "purpose": source.get("purpose"),
        "type": source.get("type"),
    }
    cleaned = {key: value for key, value in mapping.items() if value is not None}
    return cleaned or None


def _build_collateral_section(
    collateral_payload: Any,
    valuation: Optional[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    original: Optional[Any]
    if isinstance(collateral_payload, list):
        original = _safe_copy(collateral_payload[0]) if collateral_payload else None
    elif isinstance(collateral_payload, dict):
        original = _safe_copy(collateral_payload)
    else:
        original = None

    valuation_copy = _safe_copy(valuation) if valuation else None
    if isinstance(valuation_copy, dict) and "risk_score" in valuation_copy:
        valuation_copy = {k: v for k, v in valuation_copy.items() if k != "risk_score"}

    if not original and not valuation_copy:
        return None

    section: Dict[str, Any] = {}
    if original:
        section["original_payload"] = original

    if isinstance(valuation_copy, dict):
        section["valuation"] = valuation_copy
        predicted_value = None
        if "value" in valuation_copy:
            predicted_value = valuation_copy.get("value")
        if "estimatedValue" in valuation_copy:
            predicted_value = valuation_copy.get("estimatedValue")
        if predicted_value is not None:
            section["predicted_value_mnt"] = predicted_value

        valuation_details = valuation_copy.get("valuation")
        if isinstance(valuation_details, dict):
            details_copy = _safe_copy(valuation_details)
            details_copy.pop("risk_score", None)
            section["valuation_details"] = details_copy
            raw_response = details_copy.get("raw_response")
            if raw_response is not None:
                section["ml_response_raw"] = raw_response
            ml_response = details_copy.get("ml_response")
            if ml_response is not None:
                section["ml_response_json"] = ml_response

        market = valuation_copy.get("market")
        if isinstance(market, dict):
            section["market_insights"] = _safe_copy(market)

    elif valuation_copy is not None:
        section["valuation"] = valuation_copy

    return section


def _compute_bank_summary(
    parser_output: Dict[str, Any],
    documents: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    rows = parser_output.get("rows") or []
    monthly_totals: Dict[str, float] = defaultdict(float)
    first_date: Optional[datetime] = None
    last_date: Optional[datetime] = None

    for row in rows:
        if not isinstance(row, list) or not row:
            continue
        dt_obj = _parse_timestamp(row[0])
        if dt_obj:
            if first_date is None or dt_obj < first_date:
                first_date = dt_obj
            if last_date is None or dt_obj > last_date:
                last_date = dt_obj
        credit_value = _to_float(row[4]) if len(row) > 4 else None
        if dt_obj and credit_value and credit_value > 0:
            month_key = dt_obj.strftime("%Y-%m")
            monthly_totals[month_key] += credit_value

    summary: Dict[str, Any] = {}
    if monthly_totals:
        avg_income = sum(monthly_totals.values()) / len(monthly_totals)
        summary["average_monthly_income_mnt"] = round(avg_income, 2)

    period = _resolve_statement_period(parser_output, documents, first_date, last_date)
    if period:
        summary["statement_period"] = period

    return summary or None


def _resolve_statement_period(
    parser_output: Dict[str, Any],
    documents: Dict[str, Any],
    first_date: Optional[datetime],
    last_date: Optional[datetime],
) -> Optional[str]:
    stats = parser_output.get("stats") or {}
    start = _parse_timestamp(stats.get("period_from")) if stats.get("period_from") else None
    end = _parse_timestamp(stats.get("period_to")) if stats.get("period_to") else None

    period_doc = documents.get("bank_statement_period") if isinstance(documents, dict) else None
    if isinstance(period_doc, dict):
        start = start or _parse_timestamp(period_doc.get("from") or period_doc.get("from_"))
        end = end or _parse_timestamp(period_doc.get("to"))

    start = start or first_date
    end = end or last_date

    if start and end:
        return f"{start.strftime('%Y-%m')} to {end.strftime('%Y-%m')}"
    return None


def _parse_timestamp(value: Any) -> Optional[datetime]:
    if not value or isinstance(value, (int, float)):
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(text[: len(fmt)], fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        normalized = str(value).replace(",", "").strip()
        return float(normalized) if normalized else None
    except ValueError:
        return None
