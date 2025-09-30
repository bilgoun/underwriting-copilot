# bank_parser/utils.py
from datetime import datetime
import logging

logger = logging.getLogger("bank_parser.utils")


def strToFloat(value_string):
    logger.debug(f"Converting string to float: {value_string}")
    try:
        if value_string == "":
            logger.debug("Empty string provided to strToFloat")
            return None
        # Remove spaces, dashes, and commas before converting
        value_string = value_string.replace(" ", "").replace("-", "").replace(",", "")
        value_float = float(value_string)
        logger.debug(f"Converted value: {value_float}")
        return value_float
    except ValueError as e:
        logger.warning(
            f"ValueError in strToFloat for value_string '{value_string}': {str(e)}"
        )
        return None


def isValidDate(date_str, format="%Y/%m/%d"):
    logger.debug(f"Validating date string: {date_str} with format: {format}")
    if not date_str or (isinstance(date_str, str) and not date_str.strip()):
        logger.debug("Received empty date string; treating as invalid without warning")
        return False
    try:
        date = datetime.strptime(date_str, format)
        logger.debug(f"Valid date: {date}")
        return date
    except ValueError:
        logger.debug(f"Invalid date format for string: {date_str}")
        return False
