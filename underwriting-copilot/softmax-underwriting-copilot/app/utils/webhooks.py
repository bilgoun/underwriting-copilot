from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any, Dict, Optional

import requests

DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_BACKOFF_SECONDS = 2


def sign(body: bytes, secret: str) -> str:
    digest = hmac.new(secret.encode(), body, hashlib.sha256).digest()
    return base64.b64encode(digest).decode()


def emit(
    url: str,
    payload: Dict[str, Any],
    secret: str,
    timeout: int = 10,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    backoff_seconds: int = DEFAULT_BACKOFF_SECONDS,
) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode()
    signature = sign(body, secret)
    headers = {
        "Content-Type": "application/json",
        "X-Softmax-Signature": signature,
    }

    last_error: Optional[Exception] = None
    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.post(url, data=body, headers=headers, timeout=timeout)
            response.raise_for_status()
            return
        except requests.RequestException as exc:
            last_error = exc
            if attempt == max_attempts:
                break
            time.sleep(backoff_seconds * attempt)
    if last_error:
        raise last_error
