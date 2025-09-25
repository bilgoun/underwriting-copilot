from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Callable, Generator

from prometheus_client import Counter, Histogram

jobs_created_total = Counter(
    "jobs_created_total",
    "Total underwriting jobs created",
    labelnames=("tenant_id",),
)

jobs_failed_total = Counter(
    "jobs_failed_total",
    "Total underwriting jobs failed",
    labelnames=("tenant_id",),
)

underwrite_duration_seconds = Histogram(
    "underwrite_duration_seconds",
    "Underwriting duration in seconds",
    labelnames=("tenant_id", "stage"),
)

parser_seconds = Histogram(
    "parser_seconds",
    "Bank statement parsing duration",
    labelnames=("tenant_id",),
)

collateral_seconds = Histogram(
    "collateral_seconds",
    "Collateral valuation call duration",
    labelnames=("tenant_id",),
)

llm_seconds = Histogram(
    "llm_seconds",
    "LLM memo generation duration",
    labelnames=("tenant_id",),
)

webhook_attempts_total = Counter(
    "webhook_attempts_total",
    "Total webhook attempts",
    labelnames=("tenant_id", "status"),
)

webhook_failures_total = Counter(
    "webhook_failures_total",
    "Total webhook failures",
    labelnames=("tenant_id",),
)


@contextmanager
def latency_timer(metric: Histogram, **labels: str) -> Generator[None, None, None]:
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        metric.labels(**labels).observe(elapsed)


def instrument_fn(metric: Histogram, **base_labels: str) -> Callable[[Callable[..., any]], Callable[..., any]]:
    def decorator(func: Callable[..., any]) -> Callable[..., any]:
        def wrapper(*args, **kwargs):
            with latency_timer(metric, **base_labels):
                return func(*args, **kwargs)

        return wrapper

    return decorator
