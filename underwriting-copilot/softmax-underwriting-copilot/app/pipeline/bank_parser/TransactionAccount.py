# bank_parser/TransactionAccount.py

import pandas as pd
from collections import Counter
import logging

logger = logging.getLogger("bank_parser.TransactionAccount")


def get_top_words(descriptions, n=3):
    # logger.debug(f"Getting top {n} words from descriptions")
    words = " ".join(descriptions).split()
    most_common_words = Counter(words).most_common(n)
    # logger.debug(f"Top words: {most_common_words}")
    return [word for word, _ in most_common_words]


def Transaction_Account(df):
    logger.debug("Starting Transaction_Account analysis")
    try:
        filtered_data = df.dropna(subset=["transaction_account"])
        logger.debug(
            f"Filtered data size after dropping NA in 'transaction_account': {filtered_data.shape}"
        )

        unique_accounts = filtered_data["transaction_account"].unique()
        # logger.debug(f"Unique transaction accounts: {unique_accounts}")

        account_dfs = {}
        for account in unique_accounts:
            # logger.debug(f"Processing account: {account}")
            temp_df = filtered_data[filtered_data["transaction_account"] == account][
                [
                    "transaction_date",
                    "credit_transaction",
                    "debit_transaction",
                    "description",
                ]
            ]
            # logger.debug(f"Filtered DataFrame for account {account}: {temp_df.shape}")

            temp_df["transaction_date"] = (
                pd.to_datetime(temp_df["transaction_date"])
                .dt.to_period("M")
                .dt.to_timestamp()
            )
            # logger.debug("Converted 'transaction_date' to month periods")

            def count_non_zero(series):
                return sum(1 for value in series if value > 0)

            def get_top_words_by_transaction(df, transaction_type):
                return get_top_words(df.loc[df[transaction_type] > 0, "description"])

            monthly_data = temp_df.groupby(
                pd.Grouper(key="transaction_date", freq="M")
            ).agg(
                {
                    "credit_transaction": ["sum", count_non_zero],
                    "debit_transaction": ["sum", count_non_zero],
                }
            )
            monthly_data.columns = [
                "_".join(col).strip() for col in monthly_data.columns.values
            ]
            # logger.debug(f"Aggregated monthly data: {monthly_data.shape}")

            credit_desc = (
                temp_df[temp_df["credit_transaction"] > 0]
                .groupby(pd.Grouper(key="transaction_date", freq="M"))
                .agg({"description": lambda x: get_top_words(x)})
                .rename(columns={"description": "top_words_credit"})
            )
            debit_desc = (
                temp_df[temp_df["debit_transaction"] > 0]
                .groupby(pd.Grouper(key="transaction_date", freq="M"))
                .agg({"description": lambda x: get_top_words(x)})
                .rename(columns={"description": "top_words_debit"})
            )
            # logger.debug("Extracted top words for credit and debit transactions")

            monthly_data = monthly_data.join(credit_desc, how="left").join(
                debit_desc, how="left"
            )
            # logger.debug("Merged top words into monthly data")

            monthly_data.columns = [
                "credit_sum",
                "credit_count",
                "debit_sum",
                "debit_count",
                "top_words_credit",
                "top_words_debit",
            ]
            column_order = [
                "credit_sum",
                "credit_count",
                "top_words_credit",
                "debit_sum",
                "debit_count",
                "top_words_debit",
            ]
            monthly_data = monthly_data[column_order]
            # logger.debug("Renamed and ordered monthly data columns")

            total_income = df["credit_transaction"].sum()
            total_credit_sum = monthly_data["credit_sum"].sum()
            total_credit_sum_percentage = (
                total_credit_sum / total_income if total_income != 0 else 0
            )
            # logger.debug(f"Total income: {total_income}, Total credit sum: {total_credit_sum}, Percentage: {total_credit_sum_percentage}")

            filtered_monthly_data = monthly_data[
                (monthly_data["credit_sum"] > 0) & (monthly_data["debit_sum"] > 0)
            ]
            # logger.debug(f"Filtered monthly data with positive credits and debits: {filtered_monthly_data.shape}")

            if not filtered_monthly_data.empty:
                account_dfs[account] = (
                    filtered_monthly_data,
                    total_credit_sum_percentage,
                )
                # logger.debug(f"Added account {account} to account_dfs with data shape: {filtered_monthly_data.shape}")

        logger.debug(
            f"Completed Transaction_Account analysis with {len(account_dfs)} accounts"
        )
        return account_dfs
    except Exception as e:
        logger.exception(f"Exception in Transaction_Account: {str(e)}")
        return {}
