"""Utilities for removing personally identifiable information before sharing data with LLMs."""
from __future__ import annotations

import copy
from typing import Any, Dict, List

_REDACTED_TEXT = "[REDACTED]"
_SENSITIVE_TOKENS = (
    "customer_name",
    "full_name",
    "fullname",
    "regnum",
    "citizen_id",
    "national_id",
    "account_number",
    "accountnumber",
    "account_id",
    "accountid",
    "primary_phone",
    "mobile",
    "phone",
    "email",
    "contact",
    "passport",
    "dob",
    "birth",
)


def _mask_value(value: Any) -> Any:
    if isinstance(value, str):
        return _REDACTED_TEXT
    if isinstance(value, (int, float)):
        return None
    if isinstance(value, list):
        return []
    if isinstance(value, dict):
        return {}
    return None


def _is_sensitive_key(key: str) -> bool:
    lowered = key.lower()
    return any(token in lowered for token in _SENSITIVE_TOKENS)


def _sanitize(obj: Any) -> Any:
    if isinstance(obj, dict):
        sanitized: Dict[str, Any] = {}
        for key, value in obj.items():
            if _is_sensitive_key(key):
                sanitized[key] = _mask_value(value)
            else:
                sanitized[key] = _sanitize(value)
        return sanitized
    if isinstance(obj, list):
        return [_sanitize(item) for item in obj]
    return obj


def sanitize_for_llm(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Return a copy of ``payload`` with PII fields masked or removed."""
    sanitized = copy.deepcopy(payload)

    bank_summary = sanitized.get("bank_statement_summary")
    if isinstance(bank_summary, dict):
        bank_summary.pop("customer_name", None)
        bank_summary.pop("account_number", None)
        if "sample_rows" in bank_summary:
            bank_summary["sample_rows"] = []

    sanitized = _sanitize(sanitized)
    return sanitized


__all__ = ["sanitize_for_llm"]
