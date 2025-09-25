from __future__ import annotations

from typing import Any, Dict

import httpx
import structlog

from ..config import get_settings
from .market_search import derive_market_value

logger = structlog.get_logger("pipeline.collateral")


class CollateralClient:
    def __init__(self, base_url: str | None = None, timeout: int | None = None) -> None:
        settings = get_settings()
        self.base_url = str(base_url or settings.collateral_api_url).rstrip('/')
        self.timeout = timeout or settings.collateral_api_timeout
        self.sandbox = settings.sandbox_mode
        self.api_key = settings.collateral_api_key

    def valuate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        market = derive_market_value(payload)
        response = self._compose_response(payload, market)

        # Fall back to remote collateral API only if market data is unavailable
        if (
            response.get("source") == "declared_fallback"
            and not self.sandbox
            and self.api_key
        ):
            collateral_payload = payload.get("collateral", {})
            if not collateral_payload:
                raise RuntimeError("Collateral payload is required for valuation")
            try:
                api_response = self._call_remote(collateral_payload)
            except httpx.HTTPError as exc:
                logger.warning("collateral_api_error", error=str(exc))
            else:
                response.update(
                    {
                        "value": api_response.get("value", response.get("value")),
                        "confidence": api_response.get("confidence", response.get("confidence", 0.8)),
                        "source": "remote_api",
                        "risk_score": api_response.get("risk_score", response.get("risk_score")),
                        "market": response.get("market"),
                    }
                )

        return response

    def _call_remote(self, collateral_payload: Dict[str, Any]) -> Dict[str, Any]:
        headers = {
            "Content-Type": "application/json",
            "X-API-KEY": self.api_key,
        }

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/api/predict-price/",
                json=dict(collateral_payload),
                headers=headers,
            )
            response.raise_for_status()
            return response.json()

    def _compose_response(self, payload: Dict[str, Any], market: Dict[str, Any]) -> Dict[str, Any]:
        collateral_payload = payload.get("collateral", {})
        declared = float(collateral_payload.get("declared_value") or 0)

        estimated_value = market.get("estimated_value_mnt")
        samples = market.get("samples", 0)
        confidence = float(market.get("confidence") or 0.0)

        if estimated_value:
            value = float(estimated_value)
            source = "web_search"
            confidence = max(confidence, 0.55 if samples else 0.5)
        else:
            value = declared
            source = "declared_fallback"
            if value:
                confidence = max(confidence, 0.35)

        risk_score = _risk_from_values(declared_value=declared, estimated_value=value, samples=samples)

        return {
            "value": value,
            "currency": "MNT",
            "confidence": round(confidence, 2),
            "source": source,
            "risk_score": risk_score,
            "market": market,
        }


def valuate_collateral(payload: Dict[str, Any]) -> Dict[str, Any]:
    client = CollateralClient()
    return client.valuate(payload)


def _risk_from_values(*, declared_value: float, estimated_value: float, samples: int) -> float:
    if not estimated_value:
        return 0.5
    declared_value = declared_value or estimated_value
    ratio = declared_value / estimated_value if estimated_value else 1
    distance = abs(1 - ratio)
    sample_penalty = 0.15 if samples and samples < 5 else 0.05
    risk = min(0.95, max(0.05, distance + sample_penalty))
    return round(risk, 2)
