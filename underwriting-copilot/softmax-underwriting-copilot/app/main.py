from __future__ import annotations

import time
import uuid

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from .config import get_settings
from .logging import configure_logging
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
        try:
            response = await call_next(request)
        except Exception:
            logger.exception("request_error", path=request.url.path, method=request.method)
            structlog.contextvars.clear_contextvars()
            raise
        duration = time.perf_counter() - start
        logger.info(
            "request",
            path=request.url.path,
            method=request.method,
            status_code=getattr(response, "status_code", 500),
            duration_ms=int(duration * 1000),
        )
        structlog.contextvars.clear_contextvars()

        response.headers[settings.request_id_header] = request_id
        return response


app = FastAPI(title=settings.app_name, version="0.1.0")
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
