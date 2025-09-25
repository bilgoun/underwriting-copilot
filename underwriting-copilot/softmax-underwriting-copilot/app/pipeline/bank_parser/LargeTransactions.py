# ─────────────────────────────────────────────────────────────
# bank_parser/LargeTransactions.py  (threshold constant)
# ─────────────────────────────────────────────────────────────
import pandas as pd
import plotly.express as px
import logging
from .constants import LARGE_TX_THRESHOLD

logger = logging.getLogger(__name__)


def _scatter(df, column: str, title: str):
    fig = px.scatter(
        df,
        x="transaction_date",
        y=column,
        color="transaction_type",
        hover_data=["description", "transaction_date"],
        labels={"transaction_date": "Огноо", column: "Үнийн Дүн"},
        title=title,
    )
    fig.update_traces(marker=dict(size=10))
    fig.update_layout(xaxis_title="Огноо", yaxis_title="Үнийн Дүн")
    fig.update_xaxes(tickformat="%Y-%m-%d", tickangle=-45)
    return fig


def filter_debit_transactions(data):
    try:
        df = data[data["debit_transaction"] > LARGE_TX_THRESHOLD].sort_values(
            by="debit_transaction", ascending=False
        )
        df["transaction_type"] = "Зарлага"
        return df, _scatter(df, "debit_transaction", "Зарлагын Хэмжээ")
    except Exception:
        logger.exception("filter_debit_transactions failed")
        import matplotlib.pyplot as plt

        return pd.DataFrame(), plt.Figure()


def filter_credit_transactions(data):
    try:
        df = data[data["credit_transaction"] > LARGE_TX_THRESHOLD].sort_values(
            by="credit_transaction", ascending=False
        )
        df["transaction_type"] = "Орлого"
        return df, _scatter(df, "credit_transaction", "Орлогын Хэмжээ")
    except Exception:
        logger.exception("filter_credit_transactions failed")
        import matplotlib.pyplot as plt

        return pd.DataFrame(), plt.Figure()
