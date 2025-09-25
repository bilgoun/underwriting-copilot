# bank_parser/PredictIncExp.py
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import logging
import math


logger = logging.getLogger("bank_parser.PredictIncExp")


def compute_income_expense_regression(df):
    """
    If any rows have 'bank_type' == 'GOLOMT', we use 'month_1' for grouping
    to avoid collisions. Otherwise we use 'month'.
    """

    # 1) Convert transaction_date to datetime
    df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")

    # 2) Decide the column name for grouping
    if "bank_type" in df.columns and df["bank_type"].eq("GOLOMT").any():
        month_col = "month_1"
    else:
        month_col = "month"

    # 3) Drop any old column if it exists
    if month_col in df.columns:
        df.drop(columns=[month_col], inplace=True)

    # 4) Add the grouping column
    df[month_col] = df["transaction_date"].dt.to_period("M").dt.to_timestamp()

    # 5) Group by that column using as_index=False so we don’t need reset_index()
    monthly_data = (
        df.groupby(month_col, as_index=False)
        .agg(
            total_monthly_income=("credit_transaction", "sum"),
            total_monthly_expense=("debit_transaction", "sum"),
        )
        .fillna(0)
    )

    # 6) If we used 'month_1', rename it to 'month' in the result
    if month_col == "month_1":
        monthly_data.rename(columns={"month_1": "month"}, inplace=True)

    # If no rows, return empty
    if monthly_data.empty:
        return {
            "months": [],
            "actual_income": [],
            "actual_expense": [],
            "predicted_income": [],
            "predicted_expense": [],
            "future_months": [],
            "future_predicted_income": [],
            "future_predicted_expense": [],
        }

    # Sort by month
    monthly_data = monthly_data.sort_values("month").reset_index(drop=True)

    # Prepare data for regression
    month_nums = np.arange(len(monthly_data))
    income = monthly_data["total_monthly_income"].values
    expenses = monthly_data["total_monthly_expense"].values

    # Fit the regressions
    model_income = LinearRegression().fit(month_nums.reshape(-1, 1), income)
    model_expense = LinearRegression().fit(month_nums.reshape(-1, 1), expenses)

    # Predictions for existing months
    predicted_incomes = model_income.predict(month_nums.reshape(-1, 1))
    predicted_expenses = model_expense.predict(month_nums.reshape(-1, 1))

    # Predict for 3 future months
    future_range = 3
    future_month_nums = np.arange(len(monthly_data), len(monthly_data) + future_range)
    future_incomes = model_income.predict(future_month_nums.reshape(-1, 1))
    future_expenses = model_expense.predict(future_month_nums.reshape(-1, 1))

    # Convert 'month' to strings
    month_labels = monthly_data["month"].dt.strftime("%Y-%m").tolist()

    # Create future month labels: last +1, +2, +3
    last_month = monthly_data["month"].iloc[-1]
    current_period = last_month.to_period("M")
    future_month_labels = []
    for i in range(future_range):
        next_period = current_period + (i + 1)
        future_month_labels.append(str(next_period))

    return {
        "months": month_labels,
        "actual_income": income.tolist(),
        "actual_expense": expenses.tolist(),
        "predicted_income": predicted_incomes.tolist(),
        "predicted_expense": predicted_expenses.tolist(),
        "future_months": future_month_labels,
        "future_predicted_income": future_incomes.tolist(),
        "future_predicted_expense": future_expenses.tolist(),
    }


# def daily_pattern(df):
#     logger.debug("Analyzing daily pattern")
#     try:
#         df['transaction_date'] = pd.to_datetime(df['transaction_date'])

#         hour_bins = list(range(0, 25, 3))
#         hour_labels = [f"{i}-{i+3}" for i in range(0, 24, 3)]
#         df['hour_bin'] = pd.cut(df['transaction_date'].dt.hour, bins=hour_bins, labels=hour_labels, right=False)

#         average_balances = df.groupby('hour_bin')['ending_balance'].mean()

#         fig, ax = plt.subplots(figsize=(12, 6))
#         average_balances.plot(kind='bar', ax=ax, color='skyblue')
#         ax.set_title('Average Ending Balance by 3-Hour Intervals')
#         ax.set_xlabel('3-Hour Interval')
#         ax.set_ylabel('Average Ending Balance')
#         ax.set_xticklabels(hour_labels, rotation=45, ha='right', fontsize=10)

#         plt.tight_layout()
#         return fig
#     except Exception as e:
#         logger.exception(f"Exception in daily_pattern: {str(e)}")
#         return plt.Figure()
