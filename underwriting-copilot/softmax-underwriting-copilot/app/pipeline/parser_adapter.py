from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any, Dict, List, Optional

from .bank_parser import DataHandler  # noqa: F401 - ensures parsers register
from .bank_parser.registry import detect_bank


class ParserAdapterError(RuntimeError):
    pass


_DATE_FORMATS = [
    "%Y-%m-%d",
    "%d.%m.%Y",
    "%Y/%m/%d",
]


def _parse_date(candidate: str) -> Optional[dt.date]:
    for fmt in _DATE_FORMATS:
        try:
            return dt.datetime.strptime(candidate, fmt).date()
        except ValueError:
            continue
    return None


def parse(pdf_path: str) -> Dict[str, Any]:
    path = Path(pdf_path)
    if not path.exists():
        raise ParserAdapterError(f"PDF path not found: {pdf_path}")

    rows: List[List[Any]]
    bank_code: Optional[str]
    customer_name: Optional[str]
    account_number: Optional[str]

    try:
        rows, bank_code, customer_name, account_number = detect_bank(str(path))
    except Exception as exc:  # pragma: no cover - defensive
        raise ParserAdapterError("bank_parser failed") from exc

    rows = rows or []
    bank_code = bank_code or "UNKNOWN"
    customer_name = customer_name or ""
    account_number = account_number or ""

    dates = [_parse_date(str(row[0])) for row in rows if row and isinstance(row[0], str)]
    dates = [d for d in dates if d is not None]

    stats = {
        "row_count": len(rows),
        "period_from": dates[0].isoformat() if dates else None,
        "period_to": dates[-1].isoformat() if dates else None,
    }

    return {
        "bank_code": bank_code,
        "customer_name": customer_name,
        "account_number": account_number,
        "rows": rows,
        "stats": stats,
    }
