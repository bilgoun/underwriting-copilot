# bank_parser/NightTime.py

import pandas as pd
import logging

logger = logging.getLogger("bank_parser.NightTime")


def filter_night_transactions(data):
    logger.debug("Filtering night transactions")
    try:
        data["transaction_date"] = pd.to_datetime(data["transaction_date"])
        # ogger.debug("Converted 'transaction_date' to datetime")

        filtered_data = data[
            (data["transaction_date"].dt.hour >= 22)
            | (data["transaction_date"].dt.hour < 6)
        ]
        # logger.debug(f"Filtered night transactions count: {filtered_data.shape[0]}")

        filtered_data = filtered_data.sort_values(
            by="credit_transaction", ascending=False
        )
        # logger.debug("Sorted night transactions in descending order by 'credit_transaction'")

        return filtered_data
    except Exception as e:
        logger.exception(f"Exception in filter_night_transactions: {str(e)}")
        return pd.DataFrame()
