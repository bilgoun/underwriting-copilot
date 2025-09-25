# ─────────────────────────────────────────────────────────────
# bank_parser/AnalyzeDescription.py  (IGNORE_TOKENS)
# ─────────────────────────────────────────────────────────────
import pandas as pd
import logging
import re
from collections import Counter, defaultdict
from .constants import IGNORE_TOKENS
from .utils import isValidDate, strToFloat

logger = logging.getLogger(__name__)

ignore_keywords = {
    "хаанаас",
    "eb",
    "ухаалаг",
    "мэдээ",
    "үйлчилгээний",
    "хураамж",
    "апп-р",
    "хийсэн",
    "гүйлгээний",
    "320000",
    "390000",
    "040000",
    "150000",
    "520000",
}


def tokenize(text):
    text = text.lower()
    text = re.sub("[^a-zA-Z0-9\sä-яА-ЯёЁөӨүҮ]", "", text)
    tokens = [t for t in text.split() if t not in IGNORE_TOKENS]
    return tokens


def contains_word(description, word):
    tokens = tokenize(description)
    result = word in tokens
    # logger.debug(f"Checking if word '{word}' is in tokens: {result}")
    return result


def analyze_customer_data(customer_id, data):
    logger.debug(f"Analyzing data for customer_id: {customer_id}")
    try:
        customer_data = data[data["customer_id"] == customer_id]
        # logger.debug(f"Filtered data size: {customer_data.shape}")

        context = defaultdict(lambda: {"preceding": Counter(), "following": Counter()})

        for description in customer_data["description"].dropna():
            tokens = tokenize(description)
            # logger.debug(f"Processing description: {description}")
            if len(tokens) == 1:
                word = tokens[0]
                context[word]["preceding"]
                context[word]["following"]
                # logger.debug(f"Single token '{word}' found")
            else:
                for i, word in enumerate(tokens):
                    if i > 0:
                        preceding_tokens = tokens[max(0, i - 3) : i]
                        context[word]["preceding"].update(preceding_tokens)
                        # logger.debug(f"Updated preceding tokens for '{word}': {preceding_tokens}")
                    else:
                        context[word]["preceding"]
                    if i < len(tokens) - 1:
                        following_tokens = tokens[i + 1 : min(len(tokens), i + 4)]
                        context[word]["following"].update(following_tokens)
                        # logger.debug(f"Updated following tokens for '{word}': {following_tokens}")
                    else:
                        context[word]["following"]

        all_words = [
            word
            for description in customer_data["description"].dropna()
            for word in tokenize(description)
        ]
        word_counts = Counter(all_words)
        most_common_words = word_counts.most_common()
        # logger.debug(f"Most common words: {most_common_words}")
        df_common_words = pd.DataFrame(
            most_common_words, columns=["Давтагдсан Үгнүүд", "Давталт"]
        )

        word_transaction_sums = {}
        for word, freq in most_common_words:
            relevant_transactions = customer_data[
                customer_data["description"].apply(
                    lambda x: pd.notna(x) and contains_word(x, word)
                )
            ]
            credit_sum = relevant_transactions["credit_transaction"].sum()
            debit_sum = relevant_transactions["debit_transaction"].sum()
            total_sum = credit_sum + debit_sum
            if total_sum / freq >= 500:
                word_transaction_sums[word] = {
                    "Орлого": credit_sum,
                    "Зарлага": debit_sum,
                }
                # logger.debug(f"Word '{word}' meets the threshold with transactions: {word_transaction_sums[word]}")
        # logger.debug(f"Word transaction sums: {word_transaction_sums}")

        df_common_words["Орлого"] = df_common_words["Давтагдсан Үгнүүд"].map(
            lambda w: word_transaction_sums.get(w, {}).get("Орлого", 0)
        )
        df_common_words["Зарлага"] = df_common_words["Давтагдсан Үгнүүд"].map(
            lambda w: word_transaction_sums.get(w, {}).get("Зарлага", 0)
        )

        df_common_words = df_common_words[
            (df_common_words["Орлого"] > 0) | (df_common_words["Зарлага"] > 0)
        ]
        # logger.debug(f"Common words after filtering by transaction sums: {df_common_words.shape}")

        # Wrap all-uppercase words in a span with a class for highlighting
        df_common_words["Давтагдсан Үгнүүд"] = df_common_words[
            "Давтагдсан Үгнүүд"
        ].apply(
            lambda w: (
                f"({', '.join([f'{p}({c})' for p, c in context[w]['preceding'].most_common(3)])}) <span class='main-word'>{w.upper()}</span> ({', '.join([f'{f}({c})' for f, c in context[w]['following'].most_common(3)])})"
                if context[w]["preceding"] or context[w]["following"]
                else f"<span class='main-word'>{w.upper()}</span>"
            )
        )

        df_common_words = df_common_words[
            df_common_words["Давтагдсан Үгнүүд"].apply(
                lambda x: "()" not in x or len(x.split()) == 1
            )
        ]
        # logger.debug(f"Common words after removing entries with empty parentheses: {df_common_words.shape}")

        return df_common_words
    except Exception as e:
        logger.exception(f"Exception in analyze_customer_data: {str(e)}")
        return pd.DataFrame()
