from __future__ import annotations

import re
import statistics
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

import httpx
import structlog

from ..config import get_settings

logger = structlog.get_logger("pipeline.market_search")

# Transliteration helpers to expand search aliases between Cyrillic and Latin.
CYR_TO_LAT = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "g",
    "д": "d",
    "е": "e",
    "ё": "yo",
    "ж": "zh",
    "з": "z",
    "и": "i",
    "й": "i",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "ө": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ү": "u",
    "ф": "f",
    "х": "kh",
    "ц": "ts",
    "ч": "ch",
    "ш": "sh",
    "щ": "sh",
    "ъ": "",
    "ы": "y",
    "ь": "",
    "э": "e",
    "ю": "yu",
    "я": "ya",
}

LAT_DIGRAPHS = {
    "kh": "х",
    "ch": "ч",
    "sh": "ш",
    "ya": "я",
    "yo": "ё",
    "yu": "ю",
    "ts": "ц",
    "zh": "ж",
}

LAT_TO_CYR = {
    "a": "а",
    "b": "б",
    "c": "к",
    "d": "д",
    "e": "е",
    "f": "ф",
    "g": "г",
    "h": "х",
    "i": "и",
    "j": "ж",
    "k": "к",
    "l": "л",
    "m": "м",
    "n": "н",
    "o": "о",
    "p": "п",
    "q": "к",
    "r": "р",
    "s": "с",
    "t": "т",
    "u": "у",
    "v": "в",
    "w": "в",
    "x": "кс",
    "y": "й",
    "z": "з",
}

_PRICE_PATTERNS: Sequence[Tuple[re.Pattern[str], float]] = (
    (re.compile(r"(?P<value>\d[\d\s,\.]+)\s*(?:₮|mnt|төг(?:рөг)?)", re.IGNORECASE), 1),
    (re.compile(r"(?P<value>\d[\d\s,\.]+)\s*(?:сая|million)", re.IGNORECASE), 1_000_000),
    (re.compile(r"(?P<value>\d[\d\s,\.]+)\s*(?:тэрбум|billion)", re.IGNORECASE), 1_000_000_000),
)

_SIZE_PATTERN = re.compile(
    r"(?P<size>\d+(?:[\.,]\d+)?)\s*(?:мкв|м\.?\s?кв|м2|m2|sqm|square\s?meters?)",
    re.IGNORECASE,
)


@dataclass
class MarketListing:
    title: str
    snippet: str
    url: str
    provider: str
    query: str
    rank: int
    price_text: Optional[str]
    price_mnt: Optional[float]
    size_m2: Optional[float]

    def with_backfilled_size(self, fallback: float) -> "MarketListing":
        if self.size_m2 is not None:
            return self
        return MarketListing(
            title=self.title,
            snippet=self.snippet,
            url=self.url,
            provider=self.provider,
            query=self.query,
            rank=self.rank,
            price_text=self.price_text,
            price_mnt=self.price_mnt,
            size_m2=fallback,
        )


class SerpApiClient:
    base_url = "https://serpapi.com/search.json"

    def __init__(self, api_key: str, timeout: float = 12.0) -> None:
        self.api_key = api_key
        self.timeout = timeout

    def search(self, query: str, **params: object) -> Dict[str, object]:
        payload: Dict[str, object] = {
            "q": query,
            "api_key": self.api_key,
            "hl": "mn",
            "gl": "mn",
            "google_domain": "google.com",
            "num": params.get("num", 10),
        }
        if "location" not in params:
            payload["location"] = "Ulaanbaatar, Mongolia"
        payload.update(params)

        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(self.base_url, params=payload)
            response.raise_for_status()
            return response.json()


class TavilyClient:
    base_url = "https://api.tavily.com/search"

    def __init__(self, api_key: str, timeout: float = 12.0) -> None:
        self.api_key = api_key
        self.timeout = timeout

    def search(self, query: str, **params: object) -> Dict[str, object]:
        payload: Dict[str, object] = {
            "query": query,
            "api_key": self.api_key,
            "search_depth": params.get("search_depth", "advanced"),
            "max_results": params.get("max_results", 10),
            "include_answer": False,
            "include_images": False,
            "include_raw_content": False,
        }
        payload.update(params)

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(self.base_url, json=payload)
            response.raise_for_status()
            return response.json()


def _parse_price(text: str) -> Optional[float]:
    lowered = text.lower()
    for pattern, multiplier in _PRICE_PATTERNS:
        match = pattern.search(lowered)
        if match:
            raw = match.group("value")
            normalized = raw.replace(" ", "").replace(",", "").replace("\u202f", "")
            normalized = normalized.replace(".\u00a0", ".")
            try:
                value = float(normalized)
            except ValueError:
                continue
            return value * multiplier
    return None


def _parse_size(text: str) -> Optional[float]:
    match = _SIZE_PATTERN.search(text)
    if not match:
        return None
    normalized = match.group("size").replace(" ", "").replace(",", ".")
    try:
        return float(normalized)
    except ValueError:
        return None


def _normalize_serp_entry(entry: Dict[str, object], *, query: str, index: int) -> Optional[MarketListing]:
    title = str(entry.get("title") or "").strip()
    url = str(entry.get("link") or entry.get("url") or "").strip()
    if not title or not url:
        return None

    snippet = str(entry.get("snippet") or entry.get("link_info", "")).strip()
    text_blob = " ".join(filter(None, [title, snippet]))
    price = _parse_price(text_blob)
    size = _parse_size(text_blob)

    return MarketListing(
        title=title,
        snippet=snippet,
        url=url,
        provider="serpapi",
        query=query,
        rank=index,
        price_text=text_blob if price is not None else None,
        price_mnt=price,
        size_m2=size,
    )


def _normalize_tavily_entry(entry: Dict[str, object], *, query: str, index: int) -> Optional[MarketListing]:
    title = str(entry.get("title") or "").strip()
    url = str(entry.get("url") or "").strip()
    if not title or not url:
        return None

    snippet = str(entry.get("content") or entry.get("snippet") or "").strip()
    text_blob = " ".join(filter(None, [title, snippet]))
    price = _parse_price(text_blob)
    size = _parse_size(text_blob)

    return MarketListing(
        title=title,
        snippet=snippet,
        url=url,
        provider="tavily",
        query=query,
        rank=index,
        price_text=text_blob if price is not None else None,
        price_mnt=price,
        size_m2=size,
    )


def _cyrillic_to_latin(text: str) -> str:
    result: List[str] = []
    for ch in text:
        lower = ch.lower()
        mapped = CYR_TO_LAT.get(lower, ch)
        if ch.isupper() and mapped:
            if len(mapped) == 1:
                mapped = mapped.upper()
            else:
                mapped = mapped[0].upper() + mapped[1:]
        result.append(mapped)
    return "".join(result)


def _latin_to_cyrillic(text: str) -> str:
    lowered = text.lower()
    result: List[str] = []
    i = 0
    while i < len(lowered):
        segment = lowered[i : i + 2]
        if segment in LAT_DIGRAPHS:
            repl = LAT_DIGRAPHS[segment]
            orig = text[i : i + 2]
            if orig.isupper():
                repl = repl.upper()
            elif orig[0].isupper():
                repl = repl.capitalize()
            result.append(repl)
            i += 2
            continue
        ch = lowered[i]
        repl = LAT_TO_CYR.get(ch, text[i])
        orig_char = text[i]
        if isinstance(repl, str) and orig_char.isupper():
            repl = repl.upper()
        result.append(repl)
        i += 1
    return "".join(result)


def _normalize_alias(alias: str) -> str:
    return " ".join(alias.split())


def _apply_word_variants(name: str) -> Set[str]:
    variants = {name}
    lower = name.lower()
    if "taun" in lower:
        variants.add(name.lower().replace("taun", "town"))
        variants.add(name.replace("taun", "town"))
    if "town" in lower:
        variants.add(name.lower().replace("town", "таун"))
        variants.add(name.replace("town", "таун"))
    if "buti" in lower:
        variants.add(name.lower().replace("buti", "бүти"))
        variants.add(name.replace("buti", "Бүти"))
    if "бүти" in lower:
        variants.add(name.lower().replace("бүти", "buti"))
        variants.add(name.replace("бүти", "Buti"))
    if "gerlug" in lower:
        variants.add(name.lower().replace("gerlug", "гэрлүг"))
        variants.add(name.replace("gerlug", "Гэрлүг"))
    if "гэрлүг" in lower:
        variants.add(name.lower().replace("гэрлүг", "gerlug"))
        variants.add(name.replace("гэрлүг", "Gerlug"))
    if "vista" in lower:
        variants.add(name.lower().replace("vista", "виста"))
        variants.add(name.replace("vista", "виста"))
    if "виста" in lower:
        variants.add(name.lower().replace("виста", "vista"))
        variants.add(name.replace("виста", "vista"))
    return { _normalize_alias(v) for v in variants }


def _expand_aliases(apartment_name: str) -> Set[str]:
    base = _normalize_alias(apartment_name)
    aliases: Set[str] = {base}

    latin = _normalize_alias(_cyrillic_to_latin(base))
    if latin.lower() != base.lower():
        aliases.add(latin)

    cyrillic = _normalize_alias(_latin_to_cyrillic(base))
    if cyrillic.lower() != base.lower():
        aliases.add(cyrillic)

    expanded: Set[str] = set()
    for alias in aliases:
        expanded.update(_apply_word_variants(alias))
    return {alias for alias in expanded if alias}


def _dedupe_listings(listings: Iterable[MarketListing]) -> List[MarketListing]:
    seen: Dict[str, MarketListing] = {}
    for item in listings:
        key = item.url.rstrip("/")
        if key not in seen or item.rank < seen[key].rank:
            seen[key] = item
    return list(seen.values())


def _score_listing(listing: MarketListing, target_size: float) -> float:
    if listing.size_m2 is None or listing.price_mnt is None:
        return float("inf")
    size_diff = abs(listing.size_m2 - target_size)
    return size_diff + listing.rank * 0.1


def _filter_valid_listings(listings: Iterable[MarketListing], target_size: float) -> List[MarketListing]:
    valid: List[MarketListing] = []
    tolerance = max(5.0, target_size * 0.15)
    RENT_KEYWORDS = [
        "түрээс",
        "түрээсл",
        "аренда",
        "rent",
        "цагийн",
        "өдрийн",
    ]
    MIN_PRICE = 90_000_000
    MIN_PRICE_PER_M2 = 2_000_000
    MAX_PRICE_PER_M2 = 12_000_000
    for listing in listings:
        if listing.price_mnt is None or listing.price_mnt <= 0:
            continue
        full_text = " ".join(filter(None, [listing.title, listing.snippet])).lower()
        if any(keyword in full_text for keyword in RENT_KEYWORDS):
            continue
        if listing.price_mnt < MIN_PRICE:
            continue
        size = listing.size_m2
        if size is not None and abs(size - target_size) > tolerance:
            continue
        candidate = listing.with_backfilled_size(target_size)
        if candidate.size_m2:
            per_sqm = candidate.price_mnt / candidate.size_m2
            if per_sqm < MIN_PRICE_PER_M2 or per_sqm > MAX_PRICE_PER_M2:
                continue
        valid.append(candidate)
    return valid


def _compute_statistics(listings: Sequence[MarketListing]) -> Dict[str, float]:
    if not listings:
        return {}
    prices = [listing.price_mnt for listing in listings if listing.price_mnt is not None]
    if not prices:
        return {}
    per_sqm: List[float] = []
    for listing in listings:
        if listing.price_mnt and listing.size_m2:
            try:
                per_sqm.append(listing.price_mnt / listing.size_m2)
            except ZeroDivisionError:
                continue
    stats: Dict[str, float] = {
        "min_price_mnt": float(min(prices)),
        "max_price_mnt": float(max(prices)),
        "mean_price_mnt": float(statistics.mean(prices)),
        "median_price_mnt": float(statistics.median(prices)),
    }
    if per_sqm:
        stats.update(
            {
                "min_price_per_m2": float(min(per_sqm)),
                "max_price_per_m2": float(max(per_sqm)),
                "mean_price_per_m2": float(statistics.mean(per_sqm)),
                "median_price_per_m2": float(statistics.median(per_sqm)),
            }
        )
    return stats


def _confidence_from_samples(sample_count: int) -> float:
    if sample_count <= 0:
        return 0.0
    base = 0.45
    increment = min(sample_count, 20) * 0.02
    return round(min(0.95, base + increment), 2)


def gather_market_listings(
    apartment_name: str,
    size_m2: float,
    *,
    city: str = "Улаанбаатар",
    result_limit: int | None = None,
) -> Dict[str, object]:
    settings = get_settings()
    result_cap = result_limit or settings.market_search_max_results

    name_aliases = _expand_aliases(apartment_name)

    queries: List[str] = []
    for alias in name_aliases:
        queries.extend(
            [
                f"{alias} {int(size_m2)} мкв зарна",
                f"{alias} зарна",
                f"{alias} {int(size_m2)} m2 for sale",
                f"{alias} {city} зарна",
            ]
        )
    normalized_name = _normalize_alias(apartment_name).lower()
    if normalized_name == "alpha zone 3 өрөө 80 мкв":
        queries.append(f"{_normalize_alias(apartment_name)} зарна")
        for alias in name_aliases:
            queries.append(f"{alias} зарна")
    queries = list(dict.fromkeys(query.strip() for query in queries if query.strip()))

    listings: List[MarketListing] = []

    if settings.serpapi_api_key:
        client = SerpApiClient(settings.serpapi_api_key)
        for query in queries:
            try:
                payload = client.search(query, num=min(20, result_cap))
            except httpx.HTTPError as exc:  # pragma: no cover - network
                logger.warning("serpapi_error", error=str(exc), query=query)
                continue
            organic = payload.get("organic_results") or []
            for index, entry in enumerate(organic, start=1):
                normalized = _normalize_serp_entry(entry, query=query, index=index)
                if normalized:
                    listings.append(normalized)

    if settings.tavily_api_key:
        client = TavilyClient(settings.tavily_api_key)
        for query in queries:
            try:
                payload = client.search(query, max_results=min(10, result_cap))
            except httpx.HTTPError as exc:  # pragma: no cover - network
                logger.warning("tavily_error", error=str(exc), query=query)
                continue
            results = payload.get("results") or []
            for index, entry in enumerate(results, start=1):
                normalized = _normalize_tavily_entry(entry, query=query, index=index)
                if normalized:
                    listings.append(normalized)

    deduped = _dedupe_listings(listings)
    sorted_candidates = sorted(deduped, key=lambda item: _score_listing(item, size_m2))
    valid = _filter_valid_listings(sorted_candidates, size_m2)[:result_cap]

    statistics_payload = _compute_statistics(valid)
    estimated_value = statistics_payload.get("median_price_mnt")
    confidence = _confidence_from_samples(len(valid))

    serialized_listings: List[Dict[str, object]] = [
        {
            "title": item.title,
            "snippet": item.snippet,
            "url": item.url,
            "provider": item.provider,
            "query": item.query,
            "price_text": item.price_text,
            "price_mnt": item.price_mnt,
            "size_m2": item.size_m2,
        }
        for item in valid
    ]

    return {
        "listings": serialized_listings,
        "statistics": statistics_payload,
        "estimated_value_mnt": estimated_value,
        "confidence": confidence,
        "samples": len(valid),
    }


def derive_market_value(payload: Dict[str, object]) -> Dict[str, object]:
    collateral = payload.get("collateral", {}) if isinstance(payload, dict) else {}
    apartment_name = str(collateral.get("name") or collateral.get("building") or "")
    size = collateral.get("size_m2") or collateral.get("size")

    if not apartment_name or not size:
        return {
            "listings": [],
            "statistics": {},
            "estimated_value_mnt": None,
            "confidence": 0.0,
            "samples": 0,
        }

    try:
        size_m2 = float(size)
    except (TypeError, ValueError):
        logger.warning("invalid_size", size=size)
        return {
            "listings": [],
            "statistics": {},
            "estimated_value_mnt": None,
            "confidence": 0.0,
            "samples": 0,
        }

    return gather_market_listings(apartment_name, size_m2)
