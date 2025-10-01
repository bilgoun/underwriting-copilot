from __future__ import annotations

import structlog
from celery import Celery
from opentelemetry.metrics import Observation

from ..config import get_settings
from ..metrics import register_queue_depth_callback
from ..observability import init_observability

logger = structlog.get_logger("workers.celery")


def _register_queue_depth_metric(broker_url: str, queue_name: str) -> None:
    if not broker_url.startswith("redis"):
        return
    try:
        from redis import Redis
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.warning("queue_metric_redis_missing", error=str(exc))
        return

    client = Redis.from_url(broker_url)

    def _callback() -> list[Observation]:
        try:
            depth = client.llen(queue_name)
        except Exception as exc:  # pragma: no cover - redis connection issues
            logger.warning("queue_metric_sample_failed", error=str(exc))
            return []
        return [Observation(depth, {"queue": queue_name})]

    register_queue_depth_callback(_callback)
    logger.info("queue_metric_registered", queue=queue_name, broker=broker_url)


def create_celery() -> Celery:
    settings = get_settings()
    broker_url = settings.redis_url or "memory://"
    celery = Celery("softmax_underwriting", broker=broker_url, include=["app.workers.tasks"])
    celery.conf.update(
        task_track_started=True,
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="UTC",
    )

    if broker_url.startswith("rediss://"):
        celery.conf.broker_use_ssl = {
            "ssl_cert_reqs": "required",
        }
    init_observability("worker", instrument_celery=True)
    _register_queue_depth_metric(broker_url, celery.conf.task_default_queue or "celery")
    return celery


celery_app = create_celery()
