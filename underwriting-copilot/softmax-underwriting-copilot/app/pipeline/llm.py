from __future__ import annotations

import json
from typing import Any, Dict, Tuple

from ..config import get_settings

SYSTEM_PROMPT = (
    "Та банкны ахлах зээлийн шинжээч. Доорх JSON өгөгдлөөр шийдвэр гаргалтад туустлах "
    "богино, тодорхой, хариуцлагатай кредит мемо (Markdown) бич. Барьцаа хөрөнгийн "
    "веб хайлтын үр дүнг ашиглан эхлээд квадрат метрийн дундаж үнийг тооцоолж, түүнийгээ "
    "тодорхой тайлагна. Дараа нь тухайн үл хөдлөхийн нийт үнийг гарган дүгнэлтдээ тусга." 
)


def _sandbox_memo(features: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    applicant_section = features.get("монгол_банкны_өгөгдөл", {})
    risk_score = features.get("Risk_Score", 0.43)
    collateral_section = features.get("барьцаа_хөрөнгийн_үнэлгээний_өгөгдөл", {})
    market_section = collateral_section.get("зах_зээлийн_үнэд_суурилсан_үнэлгээ", {})
    market_stats = market_section.get("статистик", {})
    median_price = market_stats.get("median_price_mnt")
    sample_count = market_section.get("зарын_тоо") or len(market_section.get("эх_сурвалжууд", []))

    decision = "REVIEW" if risk_score > 0.4 else "APPROVE"
    interest = 18.4
    memo_lines = [
        "## Кредит Мемо (Sandbox)",
        "",
        "### Applicant",
        f"- Зээлийн хүсэлт: {features.get('хүссэн_зээлийн_хэмжээ', 'N/A')}",
        "",
        "### Income & Stability",
        f"- Дундаж сарын орлого: {features.get('дансны_хуулга_өгөгдөл', {}).get('дундаж_сарын_орлого', 'N/A')}₮",
        "",
        "### Risk Score",
        f"- Risk Score: {risk_score}",
        "",
        "### Collateral Insights",
        f"- Зах зээлийн жишиг үнэ: {median_price or collateral_section.get('үнэлгээ', 'N/A')}₮",
        f"- Зах зээлийн эх сурвалж: {collateral_section.get('эх_сурвалж', 'N/A')}",
        f"- Туршсан зарын тоо: {sample_count}",
        "",
        "### Recommendation",
        f"- {decision}",
    ]

    meta = {
        "decision": decision,
        "interest_rate_suggestion": interest,
    }
    memo_lines.append("")
    memo_lines.append(f"<!--META {json.dumps(meta, ensure_ascii=False)} -->")
    return "\n".join(memo_lines), meta


def generate_memo(features: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    settings = get_settings()
    if settings.sandbox_mode or settings.llm_provider.lower() == "sandbox":
        return _sandbox_memo(features)

    # Placeholder for real LLM integration.
    raise NotImplementedError("LLM provider integration not yet implemented")
