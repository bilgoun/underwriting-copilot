from __future__ import annotations

import os
from typing import Generator

from cryptography.fernet import Fernet
import pytest
from fastapi.testclient import TestClient

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Ensure critical env vars exist before application modules load
os.environ.setdefault("ENCRYPTION_KEY", Fernet.generate_key().decode())
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("SANDBOX_MODE", "true")

from app import main
from app.config import get_settings
from app.db import hash_api_key, hash_secret, init_db, session_scope
from app.models import Tenant


@pytest.fixture(scope="session", autouse=True)
def configure_env() -> Generator[None, None, None]:
    get_settings.cache_clear()  # type: ignore[attr-defined]
    init_db()
    yield
    get_settings.cache_clear()  # type: ignore[attr-defined]


@pytest.fixture(scope="session")
def tenant(configure_env) -> Tenant:
    with session_scope() as session:
        tenant = Tenant(
            name="Test Tenant",
            api_key_hash=hash_api_key("test-api-key"),
            tenant_secret="tenant-secret",
            webhook_secret="webhook-secret",
            oauth_client_id="client-id",
            oauth_client_secret=hash_secret("client-secret"),
            rate_limit_cfg={},
            rate_limit_rps=100,
        )
        session.add(tenant)
        session.flush()
        tenant_id = tenant.id
    with session_scope() as session:
        return session.get(Tenant, tenant_id)


@pytest.fixture()
def client(configure_env) -> TestClient:
    return TestClient(main.app)
