from __future__ import annotations

import json
from pathlib import Path

from app.pipeline import fuse

FIXTURES = Path(__file__).parents[1] / "fixtures"


def load_payload() -> dict:
    payload = json.loads((FIXTURES / "payload.json").read_text())
    payload["tenant_id"] = "tenant_test"
    payload["documents"]["bank_statement_url"] = "https://example.com/bank.pdf"
    return payload


def test_fused_features_contains_required_keys():
    payload = load_payload()
    parser_output = {
        "rows": [["2024-09-01", "", "", "", 1000000, 7000000]],
        "stats": {"period_from": "2024-09-01", "period_to": "2025-03-31"},
        "bank_code": "KHAN",
        "customer_name": "Бат",
        "account_number": "123",
    }
    collateral_output = json.loads((FIXTURES / "collateral_response.json").read_text())

    features = fuse.fuse_features(payload, parser_output, collateral_output)

    assert "монгол_банкны_өгөгдөл" in features
    assert features["Risk_Score"] == collateral_output.get("risk_score", 0.43)
    assert features["дансны_хуулга_өгөгдөл"]["дундаж_сарын_орлого"] >= 0
    assert features["барьцаа_хөрөнгийн_үнэлгээний_өгөгдөл"]["үнэлгээ"]
