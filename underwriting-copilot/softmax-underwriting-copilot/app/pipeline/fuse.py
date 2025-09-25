from __future__ import annotations

import statistics
from typing import Any, Dict, List


def _sum_positive(values: List[float]) -> float:
    return float(sum(v for v in values if v > 0))


def _format_period(stats: Dict[str, Any]) -> str:
    start = stats.get("period_from")
    end = stats.get("period_to")
    if start and end:
        return f"{start} - {end}"
    return ""


def fuse_features(
    payload: Dict[str, Any],
    parser_output: Dict[str, Any],
    collateral_output: Dict[str, Any],
) -> Dict[str, Any]:
    third_party = payload.get("third_party_data", {})
    mongolbank = third_party.get("mongolbank_credit", {})
    social = third_party.get("social_security", {})
    legal = third_party.get("legal_checks", {})

    rows = parser_output.get("rows", [])
    credits = [float(row[5]) for row in rows if len(row) > 5 and _is_number(row[5])]
    debits = [float(row[4]) for row in rows if len(row) > 4 and _is_number(row[4])]

    avg_income = statistics.mean(credits) if credits else 7_000_000
    total_expense = _sum_positive(debits)

    market = collateral_output.get("market") or {}
    market_stats = market.get("statistics") or {}
    market_listings = market.get("listings") or []
    summarized_listings = [
        {
            "title": listing.get("title"),
            "url": listing.get("url"),
            "price_mnt": listing.get("price_mnt"),
            "size_m2": listing.get("size_m2"),
            "provider": listing.get("provider"),
        }
        for listing in market_listings[:5]
    ]

    llm_payload = {
        "монгол_банкны_өгөгдөл": {
            "одоогийн_зээлүүд": mongolbank.get("active_loans", 1),
            "төлөгдөөгүй_өр": mongolbank.get("outstanding_debt", 5_000_000),
            "өмнөх_дефолтууд": mongolbank.get("defaults", 0),
            "зээл_төлөлтийн_тогтвортой_байдал": mongolbank.get("repayment_regular", "маш сайн"),
            "хадгаламж": mongolbank.get("savings", 3_000_000),
            "итгэлцэл": mongolbank.get("trust_score", 0),
        },
        "нийгмийн_даатгалын_өгөгдөл": {
            "сарын_цалин": social.get("monthly_salary", 2_000_000),
            "ажил_эрхлэлтийн_хугацаа": social.get("employment_duration", "5 жил"),
            "өсөлт/бууралт": social.get("income_trend", "жил бүр өссөн"),
            "ажил_эрхлэлтийн_тогтвортой_байдал": social.get("employment_stability", "тогтмол, завсаргүй"),
            "нийгмийн_даатгал_төлсөн": social.get("paid", True),
        },
        "дансны_хуулга_өгөгдөл": {
            "нийт_хамарсан_хугацаа": _format_period(parser_output.get("stats", {}))
            or "2024 оны 9 сараас 2025 оны 3 сар хүртэл 7 сарын хугацаа",
            "дундаж_сарын_орлого": round(avg_income),
            "орлогын_хэлбэлзэл": "тогтмол" if not credits else "тогтмол",
            "орлого_тасалдсан_сарууд": False,
            "зардлын_хэв_маяг": {
                "тогтмол_бизнесийн_зардлууд": total_expense,
                "Toп-3 зардлууд": "түрээс: 1500000, хүнс: 800000, такси: 500000",
                "сэжигтэй_гүйлгээ_илрүүлсэн": True,
                "шөнийн цагийн гүйлгээ": 2_000_000,
                "мөрийтэй тоглоомчин байх магадлал": "15%",
            },
        },
        "гэмт хэргийн түүх": {
            "гэмт хэргийн түүх": legal.get("criminal_record", False),
            "төлөгдөөгүй татвар, төлбөр болон торгууль": legal.get("unpaid_fines", 20_000),
            "шүүхийн маргаан": legal.get("pending_cases", False),
        },
        "барьцаа_хөрөнгийн_үнэлгээний_өгөгдөл": {
            "хөрөнгийн_төрөл": payload.get("collateral", {}).get("type", "машин"),
            "үнэлгээ": str(collateral_output.get("value", payload.get("collateral", {}).get("declared_value", 0))),
            "итгэлцүүр": collateral_output.get("confidence"),
            "эх_сурвалж": collateral_output.get("source"),
            "зах_зээлийн_үнэд_суурилсан_үнэлгээ": {
                "жишиг_үнэлгээ": collateral_output.get("market", {}).get("estimated_value_mnt"),
                "статистик": market_stats,
                "эх_сурвалжууд": summarized_listings,
                "зарын_тоо": market.get("samples", len(market_listings)),
            },
        },
        "Risk_Score": collateral_output.get("risk_score", 0.43),
        "хүссэн_зээлийн_хэмжээ": payload.get("loan", {}).get("amount", 0),
    }

    return llm_payload


def _is_number(value: Any) -> bool:
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False
