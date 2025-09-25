from __future__ import annotations

import datetime as dt
from statistics import mean, pstdev
from typing import Any, Dict, Iterable, List, Optional

import numpy as np
import pandas as pd

from .bank_parser.MonthlyBalances import filter_by_keywords, prepare_monthly_balances
from .bank_parser.NightTime import filter_night_transactions
from .bank_parser.TransactionAccount import Transaction_Account

__all__ = ["normalize"]


def normalize(
    *,
    loan_request: Dict[str, Any],
    credit_bureau: Dict[str, Any],
    social_insurance: Dict[str, Any],
    bank_statement: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Aggregate heterogeneous raw data into a single underwriting snapshot."""

    income = _compute_income(social_insurance)
    obligations = _compute_obligations(credit_bureau)
    proposed = _extract_proposed_loan(loan_request)
    post_loan = _compute_post_loan(obligations, proposed, income)
    credit_profile = _extract_credit_profile(credit_bureau)
    collateral = _build_collateral_check(loan_request, proposed)
    bank_package = _build_bank_statement_insights(bank_statement)

    snapshot = {
        "income": income,
        "existingDebtObligationsMNT": obligations,
        "proposedLoan": proposed,
        "postLoanDebtService": post_loan,
        "creditProfile": credit_profile,
        "collateralCheck": collateral,
        "bankStatement": bank_package,
        "дансны_хуулга_өгөгдөл": bank_package["summary"],
    }

    return snapshot


def _compute_income(social_insurance: Dict[str, Any], months: int = 12) -> Dict[str, int]:
    records = (
        social_insurance.get("response", {}).get("listData")
        if social_insurance else None
    )
    if not records:
        return {"avgGrossMonthlyMNT": 0, "assumedNetMonthlyMNT": 0}

    cleaned: List[Dict[str, float]] = []
    for entry in records:
        salary = _coerce_float(entry.get("salary"))
        if salary <= 0:
            continue
        cleaned.append(
            {
                "year": int(entry.get("year", 0) or 0),
                "month": int(entry.get("month", 0) or 0),
                "salary": salary,
                "shim": _coerce_float(entry.get("shim")),
            }
        )

    cleaned.sort(key=lambda item: (item["year"], item["month"]))
    window = cleaned[-months:] if months else cleaned
    if not window:
        return {"avgGrossMonthlyMNT": 0, "assumedNetMonthlyMNT": 0}

    gross_values = [item["salary"] for item in window if item["salary"] > 0]
    net_values = []
    for item in window:
        salary = item["salary"]
        shim = item.get("shim", 0.0) or 0.0
        if shim > 0:
            net_values.append(max(salary - shim, 0.0))
        else:
            net_values.append(salary * 0.85)

    gross_avg = _safe_mean(gross_values)
    net_avg = _safe_mean(net_values) if net_values else gross_avg * 0.85

    return {
        "avgGrossMonthlyMNT": int(round(gross_avg)),
        "assumedNetMonthlyMNT": int(round(net_avg)),
    }


def _compute_obligations(credit_bureau: Dict[str, Any]) -> Dict[str, int]:
    accounts = credit_bureau.get("accounts", []) if credit_bureau else []

    def _find_amount(account_type: str, field: str) -> float:
        for account in accounts:
            if account.get("type") == account_type:
                return _coerce_float(account.get(field))
        return 0.0

    credit_card_min = _find_amount("CREDIT_CARD", "minPaymentMNT")
    bnpl_installment = _find_amount("INSTALLMENT", "installmentMNT")
    telco_installment = _find_amount("TELECOM_INSTALLMENT", "installmentMNT")

    obligations = {
        "creditCardMin": int(round(credit_card_min)),
        "bnplInstallment": int(round(bnpl_installment)),
        "telcoInstallment": int(round(telco_installment)),
    }
    obligations["totalMonthly"] = sum(obligations.values())
    return obligations


def _extract_proposed_loan(loan_request: Dict[str, Any]) -> Dict[str, Any]:
    requested = loan_request.get("requestedLoan", {}) if loan_request else {}
    return {
        "amountMNT": int(round(_coerce_float(requested.get("amountMNT")))),
        "termMonths": int(round(_coerce_float(requested.get("termMonths")))),
        "aprPct": float(_coerce_float(requested.get("aprPct"))),
        "estimatedMonthlyInstallmentMNT": int(
            round(_coerce_float(requested.get("estimatedMonthlyInstallmentMNT")))
        ),
    }


def _compute_post_loan(
    obligations: Dict[str, int],
    proposed: Dict[str, Any],
    income: Dict[str, int],
) -> Dict[str, Any]:
    existing = obligations.get("totalMonthly", 0)
    proposed_installment = proposed.get("estimatedMonthlyInstallmentMNT", 0)
    total_monthly = existing + proposed_installment

    gross = income.get("avgGrossMonthlyMNT", 0)
    net = income.get("assumedNetMonthlyMNT", 0)

    dsr_gross = round(total_monthly / gross * 100, 1) if gross else None
    dsr_net = round(total_monthly / net * 100, 1) if net else None

    return {
        "totalMonthlyDebtMNT": total_monthly,
        "dsrVsGrossPct": dsr_gross,
        "dsrVsNetPct": dsr_net,
    }


def _extract_credit_profile(credit_bureau: Dict[str, Any]) -> Dict[str, Any]:
    score = credit_bureau.get("score", {}) if credit_bureau else {}
    summary = credit_bureau.get("summary", {}) if credit_bureau else {}
    accounts = credit_bureau.get("accounts", []) if credit_bureau else []

    card_utilization = 0.0
    for account in accounts:
        if account.get("type") == "CREDIT_CARD":
            card_utilization = _coerce_float(account.get("utilizationPct"))
            break

    return {
        "bureauScore": int(round(_coerce_float(score.get("value")))),
        "inquiries6m": int(round(_coerce_float(summary.get("numInquiriesLast6M")))),
        "cardUtilizationPct": round(card_utilization, 1) if card_utilization else 0.0,
        "dpd1to29Last12m": int(round(_coerce_float(summary.get("numDPD1to29Last12M")))),
    }


def _build_collateral_check(loan_request: Dict[str, Any], proposed: Dict[str, Any]) -> Dict[str, Any]:
    collaterals = loan_request.get("collateralOffered", []) if loan_request else []
    vehicle = next(
        (item for item in collaterals if str(item.get("type", "")).lower() == "vehicle"),
        {},
    )

    est_value = _coerce_float(
        vehicle.get("estimatedValueMNT", vehicle.get("estValueMNT"))
    )
    loan_amount = proposed.get("amountMNT", 0)
    ltv = round(loan_amount / est_value * 100, 1) if est_value else None

    vehicle_snapshot = {
        "plateNo": vehicle.get("plateNo"),
        "estValueMNT": int(round(est_value)) if est_value else 0,
        "pledged": bool(vehicle.get("pledgedElsewhere", False)),
        "taxDueMNT": int(round(_coerce_float(vehicle.get("taxDueMNT")))),
    }

    return {
        "vehicle": vehicle_snapshot,
        "immovablePropertyFound": False,
        "ltvIfVehicleOnlyPct": ltv,
    }


def _build_bank_statement_insights(
    bank_statement: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    summary_defaults: Dict[str, Any] = {
        "нийт_хамарсан_хугацаа": None,
        "дундаж_сарын_орлого": 0,
        "орлогын_хэлбэлзэл": "тогтмол",
        "орлого_тасалдсан_сарууд": False,
        "сэжигтэй_гүйлгээ_илрүүлсэн": False,
        "шөнийн цагийн гүйлгээ": 0,
    }

    meta: Dict[str, Any] = {
        "bankCode": None,
        "accountNumber": None,
        "customerName": None,
        "period": {"from": None, "to": None},
        "rowCount": 0,
        "monthsCovered": 0,
        "totalCreditMNT": 0,
        "suspiciousCreditMNT": 0,
        "repeatTransferAdjustmentMNT": 0,
        "adjustedCreditMNT": 0,
        "nightDebitMNT": 0,
        "coverageText": None,
    }

    if not bank_statement:
        return {"summary": summary_defaults, "meta": meta}

    meta["bankCode"] = bank_statement.get("bank_code")
    meta["accountNumber"] = bank_statement.get("account_number")
    meta["customerName"] = bank_statement.get("customer_name")

    stats = bank_statement.get("stats") or {}
    meta["period"] = {
        "from": stats.get("period_from"),
        "to": stats.get("period_to"),
    }

    rows = bank_statement.get("rows") or []
    if not rows:
        return {"summary": summary_defaults, "meta": meta}

    df = _rows_to_dataframe(rows)
    meta["rowCount"] = len(df)

    if df.empty:
        return {"summary": summary_defaults, "meta": meta}

    total_credit = float(df["credit_transaction"].sum())
    suspicious_df = filter_by_keywords(df)
    suspicious_credit = float(suspicious_df["credit_transaction"].sum()) if not suspicious_df.empty else 0.0
    if suspicious_credit <= 0.0:
        mask = df["description"].str.contains('зээл', case=False, na=False)
        suspicious_credit = float(df.loc[mask, "credit_transaction"].sum())

    suspicious_detected = bool(len(suspicious_df)) or suspicious_credit > 0

    repeat_accounts = Transaction_Account(df)
    repeat_adjustment = _estimate_repeat_transfers(repeat_accounts, total_credit)

    adjusted_total = max(total_credit - suspicious_credit - repeat_adjustment, 0.0)

    months_covered = _count_unique_months(df)
    meta["monthsCovered"] = months_covered

    avg_income = int(round(_safe_divide(adjusted_total, months_covered))) if months_covered else int(round(adjusted_total))

    coverage_text = _describe_period(df, stats)
    monthly_stats = prepare_monthly_balances(df)
    if not monthly_stats.empty and "Нийт Орлого" in monthly_stats:
        incomes = monthly_stats["Нийт Орлого"].astype(float).tolist()
    else:
        incomes = _aggregate_monthly_credit(df)

    volatility = _categorize_income_volatility(incomes)
    has_income_gaps = _has_income_gaps(incomes)

    night_df = filter_night_transactions(df)
    night_debit = (
        float(night_df["debit_transaction"].sum()) if not night_df.empty else 0.0
    )

    summary = {
        "нийт_хамарсан_хугацаа": coverage_text,
        "дундаж_сарын_орлого": avg_income,
        "орлогын_хэлбэлзэл": volatility,
        "орлого_тасалдсан_сарууд": has_income_gaps,
        "сэжигтэй_гүйлгээ_илрүүлсэн": suspicious_detected,
        "шөнийн цагийн гүйлгээ": int(round(night_debit)),
    }

    meta.update(
        {
            "totalCreditMNT": int(round(total_credit)),
            "suspiciousCreditMNT": int(round(suspicious_credit)),
            "repeatTransferAdjustmentMNT": int(round(repeat_adjustment)),
            "adjustedCreditMNT": int(round(adjusted_total)),
            "nightDebitMNT": int(round(night_debit)),
            "coverageText": coverage_text,
        }
    )

    return {"summary": summary, "meta": meta}


def _rows_to_dataframe(rows: List[Any]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(
            columns=[
                "transaction_date",
                "transaction_type",
                "reference",
                "debit_transaction",
                "credit_transaction",
                "ending_balance",
                "description",
                "transaction_account",
            ]
        )

    padded: List[List[Any]] = []
    for raw in rows:
        if not isinstance(raw, (list, tuple)):
            continue
        row = list(raw)
        if len(row) < 8:
            row.extend([None] * (8 - len(row)))
        elif len(row) > 8:
            row = row[:8]
        padded.append(row)

    if not padded:
        return pd.DataFrame(
            columns=[
                "transaction_date",
                "transaction_type",
                "reference",
                "debit_transaction",
                "credit_transaction",
                "ending_balance",
                "description",
                "transaction_account",
            ]
        )

    df = pd.DataFrame(
        padded,
        columns=[
            "transaction_date",
            "transaction_type",
            "reference",
            "debit_transaction",
            "credit_transaction",
            "ending_balance",
            "description",
            "transaction_account",
        ],
    )

    df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")
    for col in ("debit_transaction", "credit_transaction", "ending_balance"):
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    df["description"] = df["description"].fillna("").astype(str).str.strip()
    df["transaction_account"] = (
        df["transaction_account"].fillna("").astype(str).str.strip()
    )

    return df


def _count_unique_months(df: pd.DataFrame) -> int:
    if df.empty or "transaction_date" not in df:
        return 0
    periods = df["transaction_date"].dropna().dt.to_period("M").unique()
    return len(periods)


def _describe_period(df: pd.DataFrame, stats: Dict[str, Any]) -> Optional[str]:
    dates = df["transaction_date"].dropna() if "transaction_date" in df else pd.Series()
    if not dates.empty:
        start = dates.min()
        end = dates.max()
        months = (end.year - start.year) * 12 + (end.month - start.month) + 1
        return f"{start.year} оны {start.month} сараас {end.year} оны {end.month} сар хүртэл {months} сарын хугацаа"

    start_stat = _coerce_date(stats.get("period_from")) if stats else None
    end_stat = _coerce_date(stats.get("period_to")) if stats else None
    if start_stat and end_stat:
        months = (end_stat.year - start_stat.year) * 12 + (end_stat.month - start_stat.month) + 1
        return f"{start_stat.year} оны {start_stat.month} сараас {end_stat.year} оны {end_stat.month} сар хүртэл {months} сарын хугацаа"

    return None


def _aggregate_monthly_credit(df: pd.DataFrame) -> List[float]:
    if df.empty or "transaction_date" not in df:
        return []
    valid = df.dropna(subset=["transaction_date"])
    if valid.empty:
        return []
    grouped = (
        valid.groupby(valid["transaction_date"].dt.to_period("M"))["credit_transaction"]
        .sum()
        .astype(float)
    )
    return grouped.tolist()


def _categorize_income_volatility(incomes: List[float]) -> str:
    values = [v for v in incomes if v is not None]
    if len(values) < 2:
        return "тогтмол"
    avg = sum(values) / len(values)
    if avg <= 0:
        return "тогтмол"
    dispersion = pstdev(values)
    coefficient = dispersion / avg if avg else 0
    return "тогтмол" if coefficient <= 0.25 else "хэлбэлзэлтэй"


def _has_income_gaps(incomes: List[float]) -> bool:
    values = [v for v in incomes if v is not None]
    if not values:
        return False
    avg = sum(values) / len(values)
    if avg <= 0:
        return True
    threshold = max(avg * 0.5, 300_000)
    return any(v < threshold for v in values)


def _estimate_repeat_transfers(
    account_map: Dict[str, Any], total_credit: float
) -> float:
    if not account_map:
        return 0.0

    repeated = 0.0
    for payload in account_map.values():
        if not isinstance(payload, tuple) or len(payload) != 2:
            continue
        monthly_df, share = payload
        if monthly_df is None or getattr(monthly_df, "empty", True):
            continue
        if "credit_sum" not in monthly_df or "debit_sum" not in monthly_df:
            continue
        credits = pd.to_numeric(monthly_df["credit_sum"], errors="coerce").fillna(0.0)
        debits = pd.to_numeric(monthly_df["debit_sum"], errors="coerce").fillna(0.0)
        overlap = float(np.minimum(credits, debits).sum())
        if overlap <= 0:
            continue
        weight = 1.0
        try:
            if share is not None:
                numeric_share = float(share)
                if numeric_share >= 0.05:
                    weight = 1.0
                elif numeric_share > 0:
                    weight = numeric_share / 0.05
                else:
                    weight = 0.0
        except (TypeError, ValueError):
            weight = 1.0
        weight = max(0.0, min(weight, 1.0))
        repeated += overlap * weight

    if total_credit > 0:
        repeated = min(repeated, total_credit * 0.4)
    return repeated


def _coerce_float(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.replace(",", "").strip()
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
    return 0.0


def _safe_mean(values: Iterable[float]) -> float:
    data = [v for v in values if v is not None]
    return mean(data) if data else 0.0


def _coerce_date(value: Any) -> Optional[dt.date]:
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    if isinstance(value, str):
        candidates = [value, value.split(" ")[0]]
        fmts = [
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%Y.%m.%d",
            "%d.%m.%Y",
            "%m/%d/%Y",
        ]
        for candidate in candidates:
            for fmt in fmts:
                try:
                    return dt.datetime.strptime(candidate, fmt).date()
                except ValueError:
                    continue
    return None


def _safe_divide(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0
