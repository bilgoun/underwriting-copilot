from __future__ import annotations

from celery import Celery

from ..config import get_settings


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
    return celery


celery_app = create_celery()
