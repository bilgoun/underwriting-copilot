from __future__ import annotations

import logging
import sys
from typing import Any, Iterable

import structlog

PII_FIELDS: Iterable[str] = (
    "citizen_id",
    "full_name",
    "phone",
    "account_number",
    "customer_name",
    "callback_url",
)


def _mask_pii_processor(_, __, event_dict):
    for key in PII_FIELDS:
        if key in event_dict:
            event_dict[key] = "***REDACTED***"
    return event_dict


def configure_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
    )

    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        _mask_pii_processor,
        structlog.processors.JSONRenderer(),
    ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(level),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = "app") -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
