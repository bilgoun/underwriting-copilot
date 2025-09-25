#!/usr/bin/env python
"""Generate random HMAC-compatible secret strings."""

import secrets
import sys

length = 32
if len(sys.argv) > 1:
    length = int(sys.argv[1])

secret = secrets.token_hex(length)
print(secret)
