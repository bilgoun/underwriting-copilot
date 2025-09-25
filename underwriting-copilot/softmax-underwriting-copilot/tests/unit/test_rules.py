from __future__ import annotations

from app.pipeline import rules


def test_rules_decline_on_high_risk():
    features = {"Risk_Score": 0.7, "дансны_хуулга_өгөгдөл": {"дундаж_сарын_орлого": 1000000, "зардлын_хэв_маяг": {"тогтмол_бизнесийн_зардлууд": 100000}}}
    outcome = rules.evaluate(features)
    assert outcome.decision == "DECLINE"


def test_rules_approve_on_low_risk():
    features = {"Risk_Score": 0.2, "дансны_хуулга_өгөгдөл": {"дундаж_сарын_орлого": 1000000, "зардлын_хэв_маяг": {"тогтмол_бизнесийн_зардлууд": 100000}}}
    outcome = rules.evaluate(features)
    assert outcome.decision == "APPROVE"
