# ─────────────────────────────────────────────────────────────
# bank_parser/registry.py
# Holds the BANK_DETECTORS registry + decorator helpers
# ─────────────────────────────────────────────────────────────
from __future__ import annotations

import pdfplumber
from typing import Callable, List, Tuple

# Type alias for the parser return signature - Updated to include name and account
Parsed = Tuple[list, str, str, str]
CheckerFn = Callable[[list[str]], bool]
ParserFn = Callable[[str], Parsed]

BANK_DETECTORS: List[Tuple[CheckerFn, ParserFn]] = []


def register_bank(checker: CheckerFn) -> Callable[[ParserFn], ParserFn]:
    """Decorator:  @register_bank(lambda words: ...) above a parser fn"""

    def decorator(fn: ParserFn) -> ParserFn:
        BANK_DETECTORS.append((checker, fn))
        return fn

    return decorator


def detect_bank(filename: str) -> Parsed | Tuple[None, None, str, str]:
    """Iterate through registered checkers and return the first match."""
    try:
        with pdfplumber.open(filename) as pdf:
            if not pdf.pages:
                return None, None, "", ""
            first_page_text = pdf.pages[0].extract_text() or ""
    except Exception:
        # Let caller decide what to do with exceptions
        raise

    words = first_page_text.split()
    for checker, parser in BANK_DETECTORS:
        try:
            if checker(words):
                return parser(filename)
        except Exception:
            # Log inside individual parsers
            continue
    # No match - return empty strings for name and account
    return None, None, "", ""


# ---------------------------------------------------------------------------
__all__ = ["register_bank", "detect_bank", "BANK_DETECTORS"]
