from __future__ import annotations

from typing import Any, Dict, Tuple


class RuleOutcome:
    def __init__(self, decision: str, reasons: list[str]):
        self.decision = decision
        self.reasons = reasons

    def to_dict(self) -> Dict[str, Any]:
        return {"decision": self.decision, "reasons": self.reasons}


DEFAULT_DECISION = "REVIEW"


def evaluate(features: Dict[str, Any]) -> RuleOutcome:
    reasons: list[str] = []
    decision = DEFAULT_DECISION

    risk_score = features.get("Risk_Score", 0.43)
    if risk_score >= 0.6:
        decision = "DECLINE"
        reasons.append("Risk score too high")
    elif risk_score <= 0.35:
        decision = "APPROVE"

    expenses = (
        features.get("дансны_хуулга_өгөгдөл", {})
        .get("зардлын_хэв_маяг", {})
        .get("тогтмол_бизнесийн_зардлууд", 0)
    )
    income = features.get("дансны_хуулга_өгөгдөл", {}).get("дундаж_сарын_орлого", 1)
    if income and expenses / income > 0.8:
        decision = "REVIEW"
        reasons.append("High expense to income ratio")

    return RuleOutcome(decision=decision, reasons=reasons)
