# bank_parser/RawTransactions.py

import pandas as pd
import logging

logger = logging.getLogger("bank_parser.RawTransactions")


def raw_transaction(df):
    logger.debug("Processing raw transactions")
    try:
        df["transaction_date"] = pd.to_datetime(df["transaction_date"])
        # logger.debug("Converted 'transaction_date' to datetime")
        # logger.debug(f"Returning raw DataFrame with shape: {df.shape}")
        return df
    except Exception as e:
        # logger.exception(f"Exception in raw_transaction: {str(e)}")
        return pd.DataFrame()
