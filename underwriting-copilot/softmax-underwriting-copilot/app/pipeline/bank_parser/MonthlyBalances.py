# ─────────────────────────────────────────────────────────────
# bank_parser/MonthlyBalances.py  (import SUSPICIOUS_KEYWORDS)
# ─────────────────────────────────────────────────────────────
import pandas as pd
import logging
from .constants import SUSPICIOUS_KEYWORDS

logger = logging.getLogger(__name__)


def filter_by_keywords(data):
    pattern = r"\b(" + "|".join(SUSPICIOUS_KEYWORDS) + r")\b"
    return data[
        data["description"].str.contains(pattern, case=False, na=False, regex=True)
    ]


def prepare_monthly_balances(df):
    logger.debug("Preparing monthly balances")
    try:
        if df.empty:
            logger.warning("DataFrame is empty. Returning empty DataFrame.")
            return pd.DataFrame()

        df["transaction_date"] = pd.to_datetime(df["transaction_date"])
        df["month"] = df["transaction_date"].dt.to_period("M")
        # logger.debug("Converted 'transaction_date' to datetime and extracted 'month'")

        suspicious_transactions = filter_by_keywords(df)
        suspicious_sum = (
            suspicious_transactions.groupby("month")
            .agg(
                suspicious_credit=("credit_transaction", "sum"),
                suspicious_debit=("debit_transaction", "sum"),
            )
            .reset_index()
        )
        # logger.debug("Aggregated suspicious transactions by month")

        suspicious_sum["suspicious_transactions"] = (
            suspicious_sum["suspicious_credit"] + suspicious_sum["suspicious_debit"]
        )
        # logger.debug("Calculated total suspicious transactions per month")

        monthly_stats = (
            df.groupby("month")
            .agg(
                average_ending_balance=("ending_balance", "mean"),
                average_credit_transaction=("credit_transaction", "mean"),
                average_debit_transaction=("debit_transaction", "mean"),
                count_credit_transaction=(
                    "credit_transaction",
                    lambda x: (x > 0).sum(),
                ),
                count_debit_transaction=("debit_transaction", lambda x: (x > 0).sum()),
                sum_income=("credit_transaction", "sum"),
                sum_expenses=("debit_transaction", "sum"),
            )
            .reset_index()
        )
        # logger.debug("Aggregated monthly statistics")

        monthly_stats = monthly_stats.merge(
            suspicious_sum[["month", "suspicious_transactions"]], on="month", how="left"
        )
        monthly_stats["suspicious_transactions"].fillna(0, inplace=True)
        # logger.debug("Merged suspicious transactions into monthly stats")

        monthly_stats.rename(
            columns={
                "month": "Сар",
                "average_ending_balance": "Дундаж Үлдэгдэл",
                "average_credit_transaction": "Дундаж Орлого",
                "average_debit_transaction": "Дундаж Зарлага",
                "count_credit_transaction": "Орлого Гүйлгээний Тоо",
                "count_debit_transaction": "Зарлага Гүйлгээний Тоо",
                "sum_income": "Нийт Орлого",
                "sum_expenses": "Нийт Зарлага",
                "suspicious_transactions": "Сэжигтэй Гүйлгээнүүдийн Нийт Дүн",
            },
            inplace=True,
        )
        # logger.debug("Renamed columns for readability")

        column_order = [
            "Сар",
            "Дундаж Үлдэгдэл",
            "Дундаж Орлого",
            "Нийт Орлого",
            "Орлого Гүйлгээний Тоо",
            "Дундаж Зарлага",
            "Зарлага Гүйлгээний Тоо",
            "Нийт Зарлага",
            "Сэжигтэй Гүйлгээнүүдийн Нийт Дүн",
        ]
        monthly_stats = monthly_stats[column_order]
        monthly_stats = monthly_stats.sort_values(by="Сар")
        # logger.debug("Ordered and sorted monthly stats")

        numeric_cols = monthly_stats.columns[1:]
        monthly_stats[numeric_cols] = monthly_stats[numeric_cols].astype(float).round(0)
        # logger.debug("Converted numeric columns to float and rounded values")

        return monthly_stats.reset_index(drop=True)
    except Exception as e:
        logger.exception(f"Exception in prepare_monthly_balances: {str(e)}")
        return pd.DataFrame()


def summarize_transactions(df):
    logger.debug("Summarizing transactions")
    try:
        if df.empty:
            # logger.warning("DataFrame is empty. Returning empty DataFrame.")
            return pd.DataFrame(columns=["Нийт Орлого", "Нийт Сэжигтэй Гүйлгээ Дүн"])

        df["transaction_date"] = pd.to_datetime(df["transaction_date"])
        # logger.debug("Converted 'transaction_date' to datetime")

        suspicious_transactions = filter_by_keywords(df)
        total_suspicious = (
            suspicious_transactions[["credit_transaction", "debit_transaction"]]
            .sum()
            .sum()
        )
        # logger.debug(f"Total suspicious transactions sum: {total_suspicious}")

        total_credit = df["credit_transaction"].sum()
        # logger.debug(f"Total credit transactions sum: {total_credit}")

        totals_df = pd.DataFrame(
            {
                "Нийт Орлого": [total_credit],
                "Нийт Сэжигтэй Гүйлгээ Дүн": [total_suspicious],
            }
        )
        # logger.debug("Created summary DataFrame")

        return totals_df
    except Exception as e:
        logger.exception(f"Exception in summarize_transactions: {str(e)}")
        return pd.DataFrame()
