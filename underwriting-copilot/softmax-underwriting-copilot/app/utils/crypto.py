from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from cryptography.fernet import Fernet

from ..config import get_settings


@lru_cache(maxsize=1)
def get_cipher() -> Fernet:
    settings = get_settings()
    key = settings.resolved_encryption_key()
    return Fernet(key)


def encrypt_json(payload: Any) -> bytes:
    cipher = get_cipher()
    data = json.dumps(payload, ensure_ascii=False).encode()
    return cipher.encrypt(data)


def decrypt_json(blob: bytes) -> Any:
    cipher = get_cipher()
    data = cipher.decrypt(blob)
    return json.loads(data)
