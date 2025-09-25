from __future__ import annotations

import base64
import hmac
import json
import secrets
import time
from collections import defaultdict, deque
from hashlib import sha256
from threading import Lock
from typing import Deque, Iterable, Optional, Sequence

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from .config import get_settings
from .db import get_session, get_tenant_by_api_key, get_tenant_by_id
from .models import Tenant

api_key_scheme = APIKeyHeader(name="X-Api-Key", auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)
signature_header = "X-Signature"


class TenantAuthContext:
    def __init__(
        self,
        tenant_id: str,
        tenant_secret: str,
        webhook_secret: str,
        rate_limit_rps: int,
        scopes: Iterable[str],
    ) -> None:
        self.tenant_id = tenant_id
        self.tenant_secret = tenant_secret
        self.webhook_secret = webhook_secret
        self.rate_limit_rps = rate_limit_rps
        self.scopes = set(scopes)

    def ensure_scopes(self, required: Sequence[str]) -> None:
        missing = [scope for scope in required if scope not in self.scopes]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing scopes: {','.join(missing)}",
            )


class SignatureVerificationError(HTTPException):
    def __init__(self, detail: str = "Invalid signature") -> None:
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


async def get_auth_context(
    request: Request,
    api_key: Optional[str] = Depends(api_key_scheme),
    bearer: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    session: Session = Depends(get_session),
) -> TenantAuthContext:
    tenant: Optional[Tenant] = None
    scopes: Iterable[str] = []

    if api_key:
        tenant = get_tenant_by_api_key(session, api_key)
        scopes = {"underwrite:create", "underwrite:read"}
    elif bearer and bearer.scheme.lower() == "bearer":
        tenant, scopes = _resolve_bearer_credentials(session, bearer.credentials)
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    if tenant is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unknown tenant")

    context = TenantAuthContext(
        tenant_id=tenant.id,
        tenant_secret=tenant.tenant_secret,
        webhook_secret=tenant.webhook_secret,
        rate_limit_rps=tenant.rate_limit_rps,
        scopes=scopes,
    )
    request.state.tenant = context
    return context


def _resolve_bearer_credentials(session: Session, token: str) -> tuple[Optional[Tenant], Iterable[str]]:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.encryption_key, algorithms=["HS256"])
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    tenant_id = payload.get("tenant_id")
    scopes = payload.get("scope", "").split()
    expires_at = payload.get("exp", 0)
    if expires_at < int(time.time()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")

    tenant = get_tenant_by_id(session, tenant_id)
    return tenant, scopes


async def verify_inbound_signature(
    request: Request, auth_ctx: TenantAuthContext = Depends(get_auth_context)
) -> TenantAuthContext:
    signature = request.headers.get(signature_header)
    if not signature:
        raise SignatureVerificationError("Missing signature header")

    body = await request.body()
    expected = sign_payload(body, auth_ctx.tenant_secret)
    if not hmac.compare_digest(signature, expected):
        raise SignatureVerificationError("HMAC signature mismatch")

    request.state.raw_body = body
    return auth_ctx


class RateLimiter:
    def __init__(self) -> None:
        self._events: dict[str, Deque[float]] = defaultdict(deque)
        self._lock = Lock()
        self._window_seconds = 1.0

    def allow(self, tenant_id: str, rate_limit_rps: int) -> bool:
        now = time.time()
        with self._lock:
            window = self._events[tenant_id]
            while window and window[0] <= now - self._window_seconds:
                window.popleft()
            if len(window) >= rate_limit_rps:
                return False
            window.append(now)
            return True


_rate_limiter = RateLimiter()


async def enforce_rate_limit(ctx: TenantAuthContext = Depends(get_auth_context)) -> TenantAuthContext:
    if not _rate_limiter.allow(ctx.tenant_id, ctx.rate_limit_rps):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")
    return ctx


def require_scopes(*needed_scopes: str):
    async def dependency(ctx: TenantAuthContext = Depends(get_auth_context)) -> TenantAuthContext:
        ctx.ensure_scopes(needed_scopes)
        return ctx

    return dependency


def issue_access_token(tenant: Tenant, scopes: Sequence[str]) -> str:
    settings = get_settings()
    payload = {
        "tenant_id": tenant.id,
        "scope": " ".join(scopes),
        "exp": int(time.time()) + settings.oauth2_token_ttl_seconds,
        "jti": secrets.token_hex(8),
    }
    return jwt.encode(payload, settings.encryption_key, algorithm="HS256")


def sign_payload(body: bytes, secret: str) -> str:
    return base64.b64encode(hmac.new(secret.encode(), body, sha256).digest()).decode()


def sign_json(payload: dict, secret: str) -> str:
    body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode()
    return sign_payload(body, secret)
