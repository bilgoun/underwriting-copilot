from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.pipeline import normalizer

ROOT = Path(__file__).resolve().parents[2]
MOCKDATA_DIR = ROOT / "mockdata"


def _load_json(name: str) -> dict:
    return json.loads((MOCKDATA_DIR / name).read_text(encoding="utf-8"))


def test_normalize_with_mock_inputs():
    loan_request = _load_json("loanrequest.json")
    credit_bureau = _load_json("Creditbureaumock.json")
    social_insurance = _load_json("SocialInsurancemock.json")

    bank_statement = {
        "rows": [
            ["2025-01-05 10:00", "", "", 0, 3_200_000, 0, "Татваргүй цалин", "EMPLOYER-001"],
            ["2025-01-12 12:00", "", "", 1_500_000, 0, 0, "Байрны түрээс", "LANDLORD-001"],
            ["2025-02-10 09:30", "", "", 0, 3_100_000, 0, "Цалин", "EMPLOYER-001"],
            ["2025-02-18 18:00", "", "", 1_200_000, 0, 0, "Автомашины зардал", "DEALER-001"],
            ["2025-02-20 14:00", "", "", 0, 1_000_000, 0, "Гэр бүлд шилжүүлэв", "WIFE-123"],
            ["2025-02-21 16:00", "", "", 1_000_000, 0, 0, "Гэр бүл буцаалт", "WIFE-123"],
            ["2025-02-25 23:30", "", "", 2_000_000, 0, 0, "Зээлүүдийн төлбөр", "UNKNOWN"],
            ["2025-03-02 23:40", "", "", 0, 800_000, 0, "Бонус орлого", "BONUS-01"],
            ["2025-03-05 11:00", "", "", 0, 500_000, 0, "Зээлээс буцаан авсан", "UNKNOWN"],
        ],
        "stats": {"period_from": "2025-01-01", "period_to": "2025-03-31"},
        "bank_code": "KHAN",
        "customer_name": "Итгэл Даваа",
        "account_number": "1234567890",
    }

    normalized = normalizer.normalize(
        loan_request=loan_request,
        credit_bureau=credit_bureau,
        social_insurance=social_insurance,
        bank_statement=bank_statement,
    )

    income = normalized["income"]
    assert income["avgGrossMonthlyMNT"] == 4_907_003
    assert income["assumedNetMonthlyMNT"] == 3_760_423

    obligations = normalized["existingDebtObligationsMNT"]
    assert obligations["creditCardMin"] == 150_000
    assert obligations["bnplInstallment"] == 320_000
    assert obligations["telcoInstallment"] == 75_000
    assert obligations["totalMonthly"] == 545_000

    proposed = normalized["proposedLoan"]
    assert proposed["amountMNT"] == 27_000_000
    assert proposed["termMonths"] == 36
    assert proposed["estimatedMonthlyInstallmentMNT"] == 1_003_417

    post_loan = normalized["postLoanDebtService"]
    assert post_loan["totalMonthlyDebtMNT"] == 1_548_417
    assert post_loan["dsrVsGrossPct"] == pytest.approx(31.6, rel=1e-3)
    assert post_loan["dsrVsNetPct"] == pytest.approx(41.2, rel=1e-3)

    credit_profile = normalized["creditProfile"]
    assert credit_profile["bureauScore"] == 662
    assert credit_profile["inquiries6m"] == 3
    assert credit_profile["cardUtilizationPct"] == pytest.approx(85.7, rel=1e-3)
    assert credit_profile["dpd1to29Last12m"] == 1

    collateral = normalized["collateralCheck"]
    assert collateral["vehicle"]["plateNo"] == "УНН-1234"
    assert collateral["vehicle"]["estValueMNT"] == 32_000_000
    assert collateral["ltvIfVehicleOnlyPct"] == pytest.approx(84.4, rel=1e-3)

    bank_package = normalized["bankStatement"]
    summary = bank_package["summary"]
    meta = bank_package["meta"]

    assert normalized["дансны_хуулга_өгөгдөл"] == summary

    assert summary["нийт_хамарсан_хугацаа"] == "2025 оны 1 сараас 2025 оны 3 сар хүртэл 3 сарын хугацаа"
    assert summary["дундаж_сарын_орлого"] == 2_366_667
    assert summary["орлогын_хэлбэлзэл"] == "хэлбэлзэлтэй"
    assert summary["орлого_тасалдсан_сарууд"] is True
    assert summary["сэжигтэй_гүйлгээ_илрүүлсэн"] is True
    assert summary["шөнийн цагийн гүйлгээ"] == 2_000_000

    assert meta["bankCode"] == "KHAN"
    assert meta["accountNumber"] == "1234567890"
    assert meta["rowCount"] == len(bank_statement["rows"])
    assert meta["monthsCovered"] == 3
    assert meta["totalCreditMNT"] == 8_600_000
    assert meta["suspiciousCreditMNT"] == 500_000
    assert meta["repeatTransferAdjustmentMNT"] == 1_000_000
    assert meta["adjustedCreditMNT"] == 7_100_000
    assert meta["nightDebitMNT"] == summary["шөнийн цагийн гүйлгээ"]
    assert meta["coverageText"] == summary["нийт_хамарсан_хугацаа"]
