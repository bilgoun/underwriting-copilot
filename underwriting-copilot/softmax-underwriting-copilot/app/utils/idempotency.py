from __future__ import annotations

import hashlib


def build_request_fingerprint(raw_body: bytes, key_header: str | None) -> str:
    sha = hashlib.sha256()
    sha.update(raw_body)
    if key_header:
        sha.update(key_header.encode())
    return sha.hexdigest()
