from __future__ import annotations

import logging
import os
import socket
import uuid
from functools import lru_cache
from typing import Optional

from fastapi import FastAPI
from opentelemetry import metrics as otel_metrics
from opentelemetry import trace

# Robust OTLP logs exporter import (works across OTel versions)
try:
    # OTLP/HTTP logs exporter (OTel >= ~1.15, current location)
    from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
    HAS_LOG_EXPORTER = True
except Exception:
    try:
        # Fallback: OTLP/gRPC logs exporter
        from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
        HAS_LOG_EXPORTER = True
    except Exception:
        OTLPLogExporter = None  # type: ignore
        HAS_LOG_EXPORTER = False

from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
try:
    from opentelemetry.instrumentation.asgi import ASGIInstrumentor
except ImportError:
    ASGIInstrumentor = None  # type: ignore

try:
    from opentelemetry.instrumentation.celery import CeleryInstrumentor
except ImportError:
    CeleryInstrumentor = None  # type: ignore

try:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
except ImportError:
    FastAPIInstrumentor = None  # type: ignore

try:
    from opentelemetry.instrumentation.requests import RequestsInstrumentor
except ImportError:
    RequestsInstrumentor = None  # type: ignore

try:
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
except ImportError:
    SQLAlchemyInstrumentor = None  # type: ignore

try:
    from opentelemetry.instrumentation.system_metrics import SystemMetricsInstrumentor
except ImportError:
    SystemMetricsInstrumentor = None  # type: ignore
# set_logger_provider must come from the API package (not sdk)
from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs import LoggingHandler, LoggerProvider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import (
    SERVICE_INSTANCE_ID,
    SERVICE_NAME,
    SERVICE_NAMESPACE,
    SERVICE_VERSION,
    Resource,
)
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

try:  # pragma: no cover - importlib metadata not always available during tests
    from importlib.metadata import PackageNotFoundError, version
except Exception:  # pragma: no cover - fallback for legacy environments
    PackageNotFoundError = Exception

    def version(_: str) -> str:
        return "0.0.0"

from .config import get_settings

logger = logging.getLogger(__name__)


_INITIALISED_COMPONENTS: set[str] = set()
_PROMETHEUS_READER: Optional[PrometheusMetricReader] = None


def _resolve_service_version() -> str:
    try:
        return version("softmax-underwriting-copilot")
    except PackageNotFoundError:  # pragma: no cover - during local dev without packaging
        return os.getenv("SERVICE_VERSION", "0.1.0")


@lru_cache(maxsize=1)
def _resolved_resource(component: str) -> Resource:
    settings = get_settings()
    hostname = socket.gethostname()
    instance_id = f"{hostname}:{os.getpid()}:{uuid.uuid4().hex[:8]}"
    resource = Resource.create(
        {
            SERVICE_NAME: f"{settings.otel_service_name}-{component}",
            SERVICE_NAMESPACE: settings.otel_service_namespace,
            SERVICE_VERSION: _resolve_service_version(),
            SERVICE_INSTANCE_ID: instance_id,
            "deployment.environment": settings.environment,
        }
    )
    return resource


def _build_metric_readers(endpoint: str, headers: dict[str, str], resource: Resource) -> list[object]:
    global _PROMETHEUS_READER

    readers: list[object] = []

    metric_exporter = OTLPMetricExporter(
        endpoint=f"{endpoint}/v1/metrics",
        headers=headers,
    )
    readers.append(
        PeriodicExportingMetricReader(
            metric_exporter,
            export_interval_millis=get_settings().otel_metric_export_interval_ms,
        )
    )

    if _PROMETHEUS_READER is None:
        _PROMETHEUS_READER = PrometheusMetricReader()
    readers.append(_PROMETHEUS_READER)
    return readers


def init_observability(
    component: str,
    *,
    fastapi_app: Optional[FastAPI] = None,
    instrument_celery: bool = False,
) -> None:
    settings = get_settings()
    if not settings.otel_enabled:
        logger.info("otel_disabled", extra={"component": component})
        return

    if component in _INITIALISED_COMPONENTS:
        if fastapi_app is not None:
            try:
                FastAPIInstrumentor().instrument_app(fastapi_app)
            except Exception:
                logger.debug("fastapi_already_instrumented", extra={"component": component})
        return

    endpoint = settings.otel_exporter_otlp_endpoint.rstrip("/")
    headers = settings.otlp_headers()
    resource = _resolved_resource(component)

    tracer_provider = TracerProvider(resource=resource)
    span_exporter = OTLPSpanExporter(endpoint=f"{endpoint}/v1/traces", headers=headers)
    tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))
    trace.set_tracer_provider(tracer_provider)

    metric_readers = _build_metric_readers(endpoint, headers, resource)
    meter_provider = MeterProvider(resource=resource, metric_readers=metric_readers)
    otel_metrics.set_meter_provider(meter_provider)

    if SystemMetricsInstrumentor:
        SystemMetricsInstrumentor().instrument(meter_provider=meter_provider)

    # Create LoggerProvider even if we can't export logs, so LoggingHandler works locally
    logger_provider = LoggerProvider(resource=resource)
    set_logger_provider(logger_provider)

    if HAS_LOG_EXPORTER:
        log_exporter = OTLPLogExporter(
            endpoint=f"{endpoint}/v1/logs",  # for HTTP; with gRPC, env var is enough
            headers=headers,
        )
        logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))
    else:
        logger.debug("otlp_log_exporter_unavailable", extra={"component": component})

    # Attach Python logging -> OTel pipeline
    logging_handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)
    root_logger = logging.getLogger()
    root_logger.addHandler(logging_handler)

    if RequestsInstrumentor:
        RequestsInstrumentor().instrument()
    if SQLAlchemyInstrumentor:
        SQLAlchemyInstrumentor().instrument()

    if instrument_celery and CeleryInstrumentor:
        CeleryInstrumentor().instrument()

    if fastapi_app is not None:
        if FastAPIInstrumentor:
            FastAPIInstrumentor().instrument_app(fastapi_app, tracer_provider=tracer_provider)
        if ASGIInstrumentor:
            ASGIInstrumentor().instrument_app(fastapi_app)

    _INITIALISED_COMPONENTS.add(component)
    logger.info("otel_initialised", extra={"component": component, "endpoint": endpoint})


def prometheus_reader() -> Optional[PrometheusMetricReader]:
    return _PROMETHEUS_READER
