from __future__ import annotations

from functools import lru_cache
from typing import Any, Dict, List, Optional

from pydantic import AnyHttpUrl, BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class TenantBootstrap(BaseModel):
    """Configuration payload for bootstrapping default tenants."""

    name: str
    api_key: Optional[str] = None
    api_key_hash: Optional[str] = None
    webhook_secret: Optional[str] = None
    oauth_client_id: Optional[str] = None
    oauth_client_secret: Optional[str] = None
    tenant_secret: Optional[str] = None
    rate_limit_rps: int = 10


class Settings(BaseSettings):
    """Service configuration sourced from the environment."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow", env_nested_delimiter="__")

    app_name: str = Field(default="Softmax Underwriting Copilot")
    environment: str = Field(default="local")
    debug: bool = Field(default=False)
    sandbox_mode: bool = Field(default=True, alias="SANDBOX_MODE")

    port: int = Field(default=8080, alias="PORT")
    host: str = Field(default="0.0.0.0", alias="HOST")

    otel_enabled: bool = Field(default=False, alias="OTEL_ENABLED")
    otel_service_name: str = Field(default="softmax-underwriting", alias="OTEL_SERVICE_NAME")
    otel_service_namespace: str = Field(default="softmax", alias="OTEL_SERVICE_NAMESPACE")
    otel_exporter_otlp_endpoint: str = Field(default="http://otel-collector:4318", alias="OTEL_EXPORTER_OTLP_ENDPOINT")
    otel_exporter_otlp_headers: Optional[str] = Field(default=None, alias="OTEL_EXPORTER_OTLP_HEADERS")
    otel_metric_export_interval_ms: int = Field(default=60000, alias="OTEL_METRIC_EXPORT_INTERVAL_MS")

    database_url: str = Field(default="postgresql+psycopg://postgres:postgres@localhost:5432/softmax", alias="DATABASE_URL")
    redis_url: Optional[str] = Field(default=None, alias="REDIS_URL")

    api_key: Optional[str] = Field(default=None, alias="API_KEY")
    tenant_secret: Optional[str] = Field(default=None, alias="TENANT_SECRET")
    webhook_secret: Optional[str] = Field(default=None, alias="WEBHOOK_SECRET")

    encryption_key: str = Field(default="", alias="ENCRYPTION_KEY")

    llm_provider: str = Field(default="sandbox", alias="LLM_PROVIDER")
    llm_api_key: Optional[str] = Field(default=None, alias="LLM_API_KEY")

    collateral_api_url: AnyHttpUrl = Field(default="https://collateral.softmax.mn", alias="SOFTMAX_COLLATERAL_URL")
    collateral_api_key: Optional[str] = Field(default=None, alias="COLLATERAL_API_KEY")
    collateral_api_timeout: int = Field(default=20)

    serpapi_api_key: Optional[str] = Field(default=None, alias="SERPAPI_API_KEY")
    tavily_api_key: Optional[str] = Field(default=None, alias="TAVILY_API_KEY")
    market_search_max_results: int = Field(default=20, alias="MARKET_SEARCH_MAX_RESULTS")

    tmpdir: str = Field(default="/tmp", alias="TMPDIR")

    oauth2_token_ttl_seconds: int = Field(default=3600)

    prometheus_prefix: str = Field(default="softmax_underwriting")

    tenants_bootstrap: List[TenantBootstrap] = Field(default_factory=list)

    request_id_header: str = Field(default="X-Request-Id")

    def otlp_headers(self) -> dict[str, str]:
        if not self.otel_exporter_otlp_headers:
            return {}
        headers: dict[str, str] = {}
        pairs = [pair.strip() for pair in self.otel_exporter_otlp_headers.split(",") if pair.strip()]
        for pair in pairs:
            if "=" not in pair:
                continue
            key, value = pair.split("=", 1)
            headers[key.strip()] = value.strip()
        return headers

    def resolved_encryption_key(self) -> str:
        if not self.encryption_key:
            raise ValueError("ENCRYPTION_KEY must be set for field-level encryption")
        return self.encryption_key


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[arg-type]


def settings_as_dict() -> Dict[str, Any]:
    settings = get_settings()
    return settings.model_dump()
