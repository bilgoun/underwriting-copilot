from __future__ import annotations

import pytest
from fastapi import HTTPException
import base64
import hmac
from hashlib import sha256

from app.security import TenantAuthContext, sign_json, sign_payload


def test_sign_payload_matches_hmac():
    secret = "tenant-secret"
    body = b"{\"b\":\"c\"}"
    expected = base64.b64encode(hmac.new(secret.encode(), body, sha256).digest()).decode()
    assert sign_payload(body, secret) == expected


def test_sign_json_stable():
    secret = "top-secret"
    payload = {"x": 1, "y": "z"}
    first = sign_json(payload, secret)
    second = sign_json(payload, secret)
    assert first == second


def test_tenant_context_scope_check():
    ctx = TenantAuthContext("tenant", "a", "b", 10, scopes=["underwrite:read"])
    ctx.ensure_scopes(["underwrite:read"])



def test_scope_violation_raises():
    ctx = TenantAuthContext("tenant", "a", "b", 10, scopes=["underwrite:read"])
    with pytest.raises(HTTPException):
        ctx.ensure_scopes(["underwrite:create"])
