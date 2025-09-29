from __future__ import annotations

import os
from typing import Any, Dict

import httpx
import structlog

from ..config import get_settings
from .market_search import derive_market_value

logger = structlog.get_logger("pipeline.collateral")


class CollateralClient:
    def __init__(self, base_url: str | None = None, timeout: int | None = None) -> None:
        settings = get_settings()
        fallback_url = os.getenv("SOFTMAX_COLLATERAL_URL") or "https://softmax.mn"
        resolved_url = base_url or settings.collateral_api_url or fallback_url
        self.base_url = str(resolved_url).rstrip('/')
        self.timeout = timeout or settings.collateral_api_timeout
        self.sandbox = settings.sandbox_mode
        self.api_key = settings.collateral_api_key or os.getenv("COLLATERAL_API_KEY") or os.getenv("X_API_KEY")

    def valuate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # New structure: collateral is in collateralOffered array
        collateral_offered = payload.get("collateralOffered", [])
        if not collateral_offered:
            # Collateral is optional - return empty response
            logger.info("no_collateral_provided")
            return {
                "value": 0,
                "currency": "MNT",
                "confidence": 0.0,
                "source": "not_provided",
                "risk_score": 0.5,
                "note": "No collateral provided"
            }

        # Take the first collateral item
        collateral_payload = collateral_offered[0] if collateral_offered else {}

        collateral_type = collateral_payload.get("type", "").lower()

        # For vehicles: ALWAYS try ML API first, then web search fallback
        if collateral_type == "vehicle" and self.api_key:
            try:
                logger.info("processing_vehicle_collateral", vehicle_data=collateral_payload)
                api_response = self._call_remote(collateral_payload)
                response = self._create_llm_ready_response(collateral_payload, api_response)
                logger.info("ml_valuation_success", estimated_value=response.get("estimatedValue"))
                return response
            except httpx.HTTPError as exc:
                logger.warning("ml_api_error", error=str(exc))
                # Check if it's a "not found" error - if so, try web search
                if "not found" in str(exc).lower() or "404" in str(exc):
                    logger.info("vehicle_not_found_in_ml_api", brand=collateral_payload.get("brand"), model=collateral_payload.get("model"))
                    return self._try_vehicle_web_search(payload, collateral_payload)
                else:
                    # For other API errors, fall back to declared value
                    return self._create_fallback_response(collateral_payload)

        # For real estate or non-vehicle collateral: always use web search
        if collateral_type in ["real_estate", "property", "apartment", "house"]:
            logger.info("processing_real_estate_collateral", collateral_data=collateral_payload)
            market = derive_market_value(payload)
            return self._compose_response(payload, market)

        # For vehicles in sandbox mode or when ML API unavailable: use web search
        if collateral_type == "vehicle":
            logger.info("vehicle_web_search_fallback", sandbox=self.sandbox, has_api_key=bool(self.api_key))
            return self._try_vehicle_web_search(payload, collateral_payload)

        # For unknown collateral types: try web search or declared value
        logger.info("unknown_collateral_type", type=collateral_type)
        market = derive_market_value(payload)
        return self._compose_response(payload, market)

    def _try_vehicle_web_search(self, payload: Dict[str, Any], collateral_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Try web search for vehicle when ML API fails or is unavailable."""
        brand = collateral_payload.get("brand", "")
        model = collateral_payload.get("model", "")
        year = collateral_payload.get("year_made", "")

        # Create search query like "BYD Leopard 5 2024 зарна үнэ"
        search_query = f"{brand} {model}"
        if year:
            search_query += f" {year}"
        search_query += " зарна үнэ Mongolia"

        logger.info("vehicle_web_search", query=search_query)

        # Temporarily create a modified payload for web search
        temp_payload = payload.copy()
        temp_payload["collateral"] = {
            "type": "property",  # Treat as property for web search
            "name": search_query
        }

        try:
            market = derive_market_value(temp_payload)
            response = self._compose_response(temp_payload, market)

            # Convert response back to vehicle format
            return {
                "type": "Vehicle",
                "estimatedValue": int(response.get("value", 0)),
                "pledgedElsewhere": collateral_payload.get("pledgedElsewhere", False),
                "details": {
                    "brand": brand,
                    "model": model,
                    "year_made": year or 0,
                    "hurd": collateral_payload.get("hurd", ""),
                    "odometer": collateral_payload.get("odometer", 0)
                },
                "valuation": {
                    "source": "web_search",
                    "confidence": response.get("confidence", 0.4),
                    "note": f"ML API unavailable, used web search for {brand} {model}",
                    "search_query": search_query
                }
            }
        except Exception as exc:
            logger.warning("vehicle_web_search_failed", error=str(exc))
            return self._create_fallback_response(collateral_payload)

    def _create_llm_ready_response(self, collateral_payload: Dict[str, Any], ml_response: Dict[str, Any]) -> Dict[str, Any]:
        """Create LLM-ready collateral response format."""
        estimated_value = ml_response.get("value", 0)
        confidence = ml_response.get("confidence", 0.8)

        return {
            "type": "Vehicle",
            "estimatedValue": int(estimated_value),
            "pledgedElsewhere": collateral_payload.get("pledgedElsewhere", False),
            "details": {
                "brand": collateral_payload.get("brand", ""),
                "model": collateral_payload.get("model", ""),
                "year_made": collateral_payload.get("year_made", 0),
                "hurd": collateral_payload.get("hurd", ""),
                "odometer": collateral_payload.get("odometer", 0)
            },
            "valuation": {
                "source": "ml_model",
                "confidence": confidence,
                "ml_response": ml_response.get("ml_response", {}),
                "raw_response": ml_response.get("raw_response"),
            }
        }

    def _create_fallback_response(self, collateral_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create fallback response when ML API is unavailable."""
        # Banks don't provide declared values anymore
        return {
            "type": "Vehicle",
            "estimatedValue": 0,
            "pledgedElsewhere": collateral_payload.get("pledgedElsewhere", False),
            "details": {
                "brand": collateral_payload.get("brand", ""),
                "model": collateral_payload.get("model", ""),
                "year_made": collateral_payload.get("year_made", 0),
                "hurd": collateral_payload.get("hurd", ""),
                "odometer": collateral_payload.get("odometer", 0)
            },
            "valuation": {
                "source": "unavailable",
                "confidence": 0.1,
                "note": "ML API and web search both unavailable, no valuation possible"
            }
        }

    def _call_remote(self, collateral_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Transform bank vehicle data to ML API format and get prediction."""
        headers = {
            "Content-Type": "application/json",
            "X-API-KEY": self.api_key,
        }

        # Transform bank payload to ML API format
        ml_payload = self._transform_to_ml_format(collateral_payload)

        logger.info("calling_ml_api", payload=ml_payload, url=f"{self.base_url}/api/predict-price/")

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/api/predict-price/",
                json=ml_payload,
                headers=headers,
            )
            response.raise_for_status()
            raw_body = response.text
            try:
                api_response = response.json()
            except ValueError:  # pragma: no cover - defensive
                api_response = {}

            # Transform ML API response to our format
            return self._transform_ml_response(api_response, raw_body)

    def _transform_to_ml_format(self, collateral_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Transform bank's vehicle data to ML model expected format."""
        return {
            "brand": collateral_payload.get("brand", ""),
            "model": collateral_payload.get("model", ""),
            "year_made": collateral_payload.get("year_made", 0),
            "imported_year": collateral_payload.get("imported_year", collateral_payload.get("year_made", 0)),
            "odometer": collateral_payload.get("odometer", 0),
            "hurd": collateral_payload.get("hurd", ""),
            "Хурдны хайрцаг": collateral_payload.get("Хурдны хайрцаг", ""),
            "Хөдөлгүүр": collateral_payload.get("Хөдөлгүүр", ""),
            "Өнгө": collateral_payload.get("Өнгө", "")
        }

    def _transform_ml_response(self, api_response: Dict[str, Any], raw_body: str) -> Dict[str, Any]:
        """Transform ML API response to our internal format."""
        predicted_price = api_response.get("predicted_price", 0)
        confidence = api_response.get("confidence", 0.8)

        return {
            "value": float(predicted_price),
            "confidence": float(confidence),
            "source": "ml_model",
            "ml_response": api_response,
            "raw_response": raw_body,
        }

    def _compose_response(self, payload: Dict[str, Any], market: Dict[str, Any]) -> Dict[str, Any]:
        estimated_value = market.get("estimated_value_mnt")
        samples = market.get("samples", 0)
        confidence = float(market.get("confidence") or 0.0)

        if estimated_value:
            value = float(estimated_value)
            source = "web_search"
            confidence = max(confidence, 0.55 if samples else 0.5)
        else:
            value = 0
            source = "unavailable"
            confidence = 0.1

        risk_score = _risk_from_values(declared_value=0, estimated_value=value, samples=samples)

        return {
            "value": value,
            "currency": "MNT",
            "confidence": round(confidence, 2),
            "source": source,
            "risk_score": risk_score,
            "market": market,
        }


def valuate_collateral(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Main entry point for collateral valuation."""
    client = CollateralClient()
    return client.valuate(payload)


def derive_market_value(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Derive market value for vehicles using ML model API."""
    # For backward compatibility, redirect to the main valuation function
    return valuate_collateral(payload)


def _risk_from_values(*, declared_value: float, estimated_value: float, samples: int) -> float:
    if not estimated_value:
        return 0.5
    declared_value = declared_value or estimated_value
    ratio = declared_value / estimated_value if estimated_value else 1
    distance = abs(1 - ratio)
    sample_penalty = 0.15 if samples and samples < 5 else 0.05
    risk = min(0.95, max(0.05, distance + sample_penalty))
    return round(risk, 2)
