from __future__ import annotations

import time
import uuid

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from .config import get_settings
from .logging import configure_logging
from .metrics import http_request_duration_ms, http_request_errors_total, http_requests_total
from .observability import init_observability
from .routes import register_routes

settings = get_settings()
configure_logging()
logger = structlog.get_logger("app.main")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get(settings.request_id_header) or str(uuid.uuid4())
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        start = time.perf_counter()
        has_error = False
        status_code = 500
        path_template = request.url.path
        route = request.scope.get("route")
        if route is not None and getattr(route, "path", None):
            path_template = route.path
        try:
            response = await call_next(request)
            status_code = getattr(response, "status_code", 500)
        except Exception:
            has_error = True
            logger.exception("request_error", path=request.url.path, method=request.method)
            structlog.contextvars.clear_contextvars()
            raise
        duration = time.perf_counter() - start
        tenant_ctx = getattr(request.state, "tenant", None)
        tenant_id = getattr(tenant_ctx, "tenant_id", "unknown")
        metric_labels = {
            "method": request.method.upper(),
            "path": path_template,
            "status_code": str(status_code),
            "tenant_id": tenant_id,
        }
        http_requests_total.labels(**metric_labels).inc()
        http_request_duration_ms.labels(**metric_labels).observe(duration * 1000.0)
        if has_error or status_code >= 500:
            http_request_errors_total.labels(**metric_labels).inc()
        logger.info(
            "request",
            path=request.url.path,
            method=request.method,
            status_code=status_code,
            duration_ms=int(duration * 1000),
        )
        structlog.contextvars.clear_contextvars()

        response.headers[settings.request_id_header] = request_id
        return response


app = FastAPI(title=settings.app_name, version="0.1.0")
init_observability("api", fastapi_app=app)
app.add_middleware(RequestContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_routes(app)


@app.get("/")
async def root() -> dict[str, str]:
    return {"service": settings.app_name, "status": "up"}
