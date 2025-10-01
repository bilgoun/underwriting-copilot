from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from typing import Callable, Generator, Iterable, List

from opentelemetry import metrics as otel_metrics
from opentelemetry.metrics import CallbackOptions, Observation

_logger = logging.getLogger(__name__)

_METER = otel_metrics.get_meter("softmax-underwriting", version="0.1.0")


class _CounterBinding:
    def __init__(self, instrument, attributes: dict[str, str]):
        self._instrument = instrument
        self._attributes = attributes

    def inc(self, amount: float = 1.0) -> None:
        self._instrument.add(float(amount), self._attributes)


class _HistogramBinding:
    def __init__(self, instrument, attributes: dict[str, str]):
        self._instrument = instrument
        self._attributes = attributes

    def observe(self, value: float) -> None:
        self._instrument.record(float(value), self._attributes)


class CounterWrapper:
    def __init__(self, instrument):
        self._instrument = instrument

    def labels(self, **attributes: str) -> _CounterBinding:
        return _CounterBinding(self._instrument, attributes)

    def add(self, amount: float, **attributes: str) -> None:
        self._instrument.add(float(amount), attributes)


class HistogramWrapper:
    def __init__(self, instrument):
        self._instrument = instrument

    def labels(self, **attributes: str) -> _HistogramBinding:
        return _HistogramBinding(self._instrument, attributes)

    def record(self, value: float, **attributes: str) -> None:
        self._instrument.record(float(value), attributes)


jobs_created_total = CounterWrapper(
    _METER.create_counter(
        "underwriting_jobs_created_total",
        description="Total underwriting jobs created",
    )
)

jobs_failed_total = CounterWrapper(
    _METER.create_counter(
        "underwriting_jobs_failed_total",
        description="Total underwriting jobs failed",
    )
)

underwrite_duration_seconds = HistogramWrapper(
    _METER.create_histogram(
        "underwriting_duration_seconds",
        unit="s",
        description="Underwriting duration in seconds by stage",
    )
)

parser_seconds = HistogramWrapper(
    _METER.create_histogram(
        "underwriting_parser_duration_seconds",
        unit="s",
        description="Bank statement parsing duration",
    )
)

collateral_seconds = HistogramWrapper(
    _METER.create_histogram(
        "underwriting_collateral_duration_seconds",
        unit="s",
        description="Collateral valuation call duration",
    )
)

llm_seconds = HistogramWrapper(
    _METER.create_histogram(
        "underwriting_llm_duration_seconds",
        unit="s",
        description="LLM memo generation duration",
    )
)

webhook_attempts_total = CounterWrapper(
    _METER.create_counter(
        "underwriting_webhook_attempts_total",
        description="Total webhook attempts",
    )
)

webhook_failures_total = CounterWrapper(
    _METER.create_counter(
        "underwriting_webhook_failures_total",
        description="Total webhook failures",
    )
)

http_requests_total = CounterWrapper(
    _METER.create_counter(
        "http_requests_total",
        description="Total HTTP requests handled by the API",
    )
)

http_request_errors_total = CounterWrapper(
    _METER.create_counter(
        "http_request_errors_total",
        description="Total HTTP requests that returned 5xx responses",
    )
)

http_request_duration_ms = HistogramWrapper(
    _METER.create_histogram(
        "http_request_duration_ms",
        unit="ms",
        description="HTTP request latency in milliseconds",
    )
)

_QUEUE_DEPTH_CALLBACKS: list[Callable[[], Iterable[Observation]]] = []


def _queue_depth_observer(_: CallbackOptions) -> Iterable[Observation]:
    measurements: List[Observation] = []
    for callback in list(_QUEUE_DEPTH_CALLBACKS):
        try:
            values = list(callback())
        except Exception as exc:  # pragma: no cover - defensive guard
            _logger.warning("queue_depth_callback_failed", error=str(exc))
            continue
        measurements.extend(values)
    return measurements


_METER.create_observable_gauge(
    "queue_backlog",
    callbacks=[_queue_depth_observer],
    description="Number of queued underwriting tasks",
)


def register_queue_depth_callback(callback: Callable[[], Iterable[Observation]]) -> None:
    _QUEUE_DEPTH_CALLBACKS.append(callback)


@contextmanager
def latency_timer(metric: HistogramWrapper, **attributes: str) -> Generator[None, None, None]:
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        metric.labels(**attributes).observe(elapsed)


def instrument_fn(
    metric: HistogramWrapper, **base_attributes: str
) -> Callable[[Callable[..., object]], Callable[..., object]]:
    def decorator(func: Callable[..., object]) -> Callable[..., object]:
        def wrapper(*args, **kwargs):
            with latency_timer(metric, **base_attributes):
                return func(*args, **kwargs)

        return wrapper

    return decorator
