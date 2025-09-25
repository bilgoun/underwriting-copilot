from __future__ import annotations

from typing import Any, Dict

import pytest

from app.config import get_settings
from app.pipeline import collateral, market_search


def test_alias_expansion_handles_cyrillic_and_latin():
    aliases = market_search._expand_aliases("Бүти таун")
    lower_aliases = {a.lower() for a in aliases}
    assert any("buti" in alias for alias in lower_aliases)
    assert any("town" in alias for alias in lower_aliases)

    latin_aliases = market_search._expand_aliases("Gerlug Vista")
    assert any("гэрлүг" in alias for alias in latin_aliases)
    assert any("виста" in alias for alias in latin_aliases)

def _serp_sample(_: market_search.SerpApiClient, query: str, **kwargs: Any) -> Dict[str, Any]:
    return {
        "organic_results": [
            {
                "title": f"{query} - зар",
                "link": "https://example.com/serp",
                "snippet": "80 мкв орон сууц, үнэ 320 сая төгрөг",
            }
        ]
    }


def _tavily_sample(_: market_search.TavilyClient, query: str, **kwargs: Any) -> Dict[str, Any]:
    return {
        "results": [
            {
                "title": f"{query} санал", 
                "url": "https://example.com/tavily",
                "content": "Орон сууц 80 м2 талбайтай, нийт үнэ 350 сая төгрөг",
            }
        ]
    }


def test_market_search_aggregation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENCRYPTION_KEY", "a" * 44)
    monkeypatch.setenv("SERPAPI_API_KEY", "serp-key")
    monkeypatch.setenv("TAVILY_API_KEY", "tavily-key")
    get_settings.cache_clear()  # type: ignore[attr-defined]

    monkeypatch.setattr(market_search.SerpApiClient, "search", _serp_sample)
    monkeypatch.setattr(market_search.TavilyClient, "search", _tavily_sample)

    data = market_search.gather_market_listings("Хүннү 2222", 80)

    assert data["samples"] == 2
    assert data["statistics"]["median_price_mnt"] == pytest.approx(335_000_000)
    assert data["statistics"]["median_price_per_m2"] == pytest.approx(4_187_500)
    assert data["estimated_value_mnt"] == pytest.approx(335_000_000)


def test_collateral_response_uses_market(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENCRYPTION_KEY", "a" * 44)
    monkeypatch.setenv("SANDBOX_MODE", "true")
    monkeypatch.setenv("SERPAPI_API_KEY", "serp-key")
    monkeypatch.setenv("TAVILY_API_KEY", "tavily-key")
    get_settings.cache_clear()  # type: ignore[attr-defined]

    monkeypatch.setattr(market_search.SerpApiClient, "search", _serp_sample)
    monkeypatch.setattr(market_search.TavilyClient, "search", _tavily_sample)

    payload = {
        "collateral": {
            "name": "Хүннү 2222",
            "size_m2": 80,
            "declared_value": 300_000_000,
        }
    }

    result = collateral.valuate_collateral(payload)

    assert result["source"] == "web_search"
    assert result["value"] == pytest.approx(335_000_000)
    assert 0.05 <= result["risk_score"] <= 0.95
    market_info = result["market"]
    assert market_info["samples"] == 2
    assert market_info["listings"]
