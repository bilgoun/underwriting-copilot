# bank_parser/DataHandler.py
"""
Low‑level helpers and every bank‑specific parser.
All public signatures stay exactly the same as the legacy version,
so nothing else in your project needs to change.

✓ Draw‑guide helpers are de‑duplicated
✓ All “magic numbers” pulled from constants.py
✓ Registry pattern lets you add more banks with one decorator
"""

from __future__ import annotations

import logging
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path
from typing import List, Sequence, Tuple

import fitz  # PyMuPDF
import pdfplumber

from .constants import GUIDE_COLOURS, VERTICAL_GUIDES
from .registry import register_bank, detect_bank
from .utils import isValidDate, strToFloat

logger = logging.getLogger(__name__)

# ────────────────────────────────────────────────────────────
# generic PDF helper
# ────────────────────────────────────────────────────────────


def _draw_vertical_guides(
    pdf_path: str | Path,
    output_path: str | Path,
    x_coords: Sequence[float],
    *,
    colour: Tuple[float, float, float] = (0, 0, 0),
    width: float = 0.2,
) -> None:
    """
    Add thin vertical guide lines so that `pdfplumber` can
    split the page into reliable table columns.
    """
    doc = fitz.open(str(pdf_path))
    try:
        for page in doc:
            height = page.mediabox.height
            for x in x_coords:
                page.draw_line((x, 0), (x, height), color=colour, width=width)

            # extra right‑border tweaks for particular layouts
            if x_coords is VERTICAL_GUIDES["GOLOMT"]:
                page.draw_line(
                    (page.mediabox.width - 70, 0),
                    (page.mediabox.width - 70, height),
                    color=colour,
                    width=width,
                )
            if x_coords is VERTICAL_GUIDES["KHAN_KIOSK"]:
                page.draw_line(
                    (page.mediabox.width - 10, 0),
                    (page.mediabox.width - 10, height),
                    color=colour,
                    width=width,
                )

        doc.save(str(output_path))
    finally:
        doc.close()


# convenience wrappers – the rest of the code still calls these names
def draw_line_on_pdf(pdf_path, output_path):
    _draw_vertical_guides(
        pdf_path,
        output_path,
        VERTICAL_GUIDES["KHAN_LINE"],
        colour=GUIDE_COLOURS["KHAN_LINE"],
        width=0.2,
    )


def draw_khan_on_pdf(pdf_path, output_path):
    _draw_vertical_guides(
        pdf_path,
        output_path,
        VERTICAL_GUIDES["KHAN_KIOSK"],
        colour=GUIDE_COLOURS["KHAN_KIOSK"],
        width=0.1,
    )


def draw_golomt_on_pdf(pdf_path, output_path):
    _draw_vertical_guides(
        pdf_path,
        output_path,
        VERTICAL_GUIDES["GOLOMT"],
        colour=GUIDE_COLOURS["GOLOMT"],
        width=0.2,
    )


def draw_tdb_on_pdf(pdf_path, output_path):
    tmp = Path(output_path)
    _draw_vertical_guides(
        pdf_path,
        tmp,
        VERTICAL_GUIDES["TDB"],
        colour=GUIDE_COLOURS["TDB"],
        width=0.4,
    )
    # add footer line afterwards
    with fitz.open(str(tmp)) as doc:
        for page in doc:
            page.draw_line(
                (10, page.mediabox.height - 50),
                (page.mediabox.width - 10, page.mediabox.height - 50),
                color=(0, 0, 0),
                width=0.4,
            )
        doc.saveIncr()


# ╭──────────────────────────────────────────────────────────╮
# │ Khan Bank – “Printed …”                                  │
# ╰──────────────────────────────────────────────────────────╯
@register_bank(lambda w: bool(w) and w[0] == "Printed")
def getKhanData(pdf_path: str | Path) -> Tuple[List[List], str, str, str]:
    logger.info(f"[KHAN] Processing PDF: {pdf_path}")
    rows: list[list] = []
    customer_name = ""
    account_number = ""

    # Extract customer info from first page
    with pdfplumber.open(str(pdf_path)) as pdf:
        if pdf.pages:
            first_page_text = pdf.pages[0].extract_text() or ""
            logger.info(f"[KHAN] First page text length: {len(first_page_text)}")
            logger.info(f"[KHAN] First 500 chars: {first_page_text[:500]}")

            lines = first_page_text.split("\n")
            logger.info(f"[KHAN] Total lines: {len(lines)}")

            for i, line in enumerate(lines[:20]):  # Log first 20 lines
                logger.info(f"[KHAN] Line {i}: {line}")

                if "Хэрэглэгч:" in line:
                    parts = line.split("Хэрэглэгч:")
                    if len(parts) > 1:
                        # Extract only the name part, before any additional text like "Интервал"
                        customer_part = parts[1].strip()
                        if "Интервал:" in customer_part:
                            customer_name = customer_part.split("Интервал:")[0].strip()
                        else:
                            customer_name = customer_part
                        logger.info(f"[KHAN] Found customer name: '{customer_name}'")
                elif "Дансны дугаар:" in line:
                    parts = line.split("Дансны дугаар:")
                    if len(parts) > 1:
                        account_number = parts[1].strip()
                        logger.info(f"[KHAN] Found account number: '{account_number}'")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp_path = Path(tmp.name)

    try:
        draw_khan_on_pdf(pdf_path, tmp_path)

        with pdfplumber.open(str(tmp_path)) as pdf:
            for idx, page in enumerate(pdf.pages):
                crop = (20, 160 if idx == 0 else 60, page.width, page.height - 40)
                for table in page.crop(crop).extract_tables():
                    for raw in table:
                        if (
                            raw
                            and len(raw) > 8
                            and isValidDate(f"{raw[0]} {raw[1]}", "%Y/%m/%d %H:%M")
                        ):
                            row = [None] * 8
                            row[0] = isValidDate(f"{raw[0]} {raw[1]}", "%Y/%m/%d %H:%M")
                            row[1] = raw[2]
                            row[2:6] = map(strToFloat, raw[3:7])
                            row[6] = raw[7]
                            row[7] = raw[8]
                            rows.append(row)
    finally:
        tmp_path.unlink(missing_ok=True)

    logger.info(f"[KHAN] Extraction complete:")
    logger.info(f"[KHAN] - Rows found: {len(rows)}")
    logger.info(f"[KHAN] - Customer name: '{customer_name}'")
    logger.info(f"[KHAN] - Account number: '{account_number}'")

    return rows, "KHAN", customer_name, account_number


# ╭──────────────────────────────────────────────────────────╮
# │ Khan “Kiosk”                                             │
# ╰──────────────────────────────────────────────────────────╯
@register_bank(lambda w: bool(w) and w[0] == "Харилцагчийн")
def getKhanKioskData(pdf_path: str | Path) -> Tuple[List[List], str, str, str]:
    interim: list[list] = []
    final: list[list] = []
    customer_name = ""
    account_number = ""

    # Extract customer info from first page
    with pdfplumber.open(str(pdf_path)) as pdf:
        if pdf.pages:
            first_page_text = pdf.pages[0].extract_text() or ""
            lines = first_page_text.split("\n")

            for line in lines:
                if "Харилцагчийн нэр:" in line:
                    parts = line.split("Харилцагчийн нэр:")
                    if len(parts) > 1:
                        customer_name = parts[1].strip()
                elif "Дансны дугаар:" in line:
                    parts = line.split("Дансны дугаар:")
                    if len(parts) > 1:
                        account_number = parts[1].strip()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp_path = Path(tmp.name)

    try:
        draw_line_on_pdf(pdf_path, tmp_path)

        with pdfplumber.open(str(tmp_path)) as pdf:
            for idx, page in enumerate(pdf.pages):
                crop = (
                    [40, 130, page.width, page.height - 40]
                    if idx == 0
                    else [
                        30,
                        0,
                        page.width,
                        page.height - 40,
                    ]
                )
                tables = page.crop(crop, relative=False, strict=True).extract_tables(
                    {"vertical_strategy": "lines", "horizontal_strategy": "text"}
                )

                for table in tables:
                    for row in table:
                        if row == [""] * len(row):
                            continue
                        if row[0] == "" and interim:
                            interim[-1][5] += " " + row[5]
                        else:
                            interim.append(row)

        # transform to canonical 8‑column rows
        for r in interim:
            if isValidDate(f"{r[0]} {r[4]}", "%m/%d/%Y %H:%M"):
                row = [None] * 8
                row[0] = isValidDate(f"{r[0]} {r[4]}", "%m/%d/%Y %H:%M")
                row[1] = r[1]
                row[7] = r[3]
                row[6] = r[5]
                row[4] = strToFloat(r[6])
                row[3] = strToFloat(r[7])
                row[5] = strToFloat(r[8])
                final.append(row)
    finally:
        tmp_path.unlink(missing_ok=True)

    return final, "KHAN-KIOSK", customer_name, account_number


# ╭──────────────────────────────────────────────────────────╮
# │ Golomt Bank                                             │
# ╰──────────────────────────────────────────────────────────╯
@register_bank(lambda w: bool(w) and w[0] == "ГОЛОМТ")
def getGolomtData(pdf_path: str | Path) -> Tuple[List[List], str, str, str]:
    logger.info(f"[GOLOMT] Processing PDF: {pdf_path}")
    rows: list[list] = []
    customer_name = ""
    account_number = ""

    # Extract customer info from first page
    with pdfplumber.open(str(pdf_path)) as pdf:
        if pdf.pages:
            first_page_text = pdf.pages[0].extract_text() or ""
            logger.info(f"[GOLOMT] First page text length: {len(first_page_text)}")
            logger.info(f"[GOLOMT] First 800 chars: {first_page_text[:800]}")

            lines = first_page_text.split("\n")
            logger.info(f"[GOLOMT] Total lines: {len(lines)}")

            for i, line in enumerate(lines[:25]):  # Log first 25 lines
                logger.info(f"[GOLOMT] Line {i}: {line}")

                # Try multiple patterns for account number due to OCR issues
                if "Данс:" in line or "AДcаcнoсu:nt:" in line or "Account:" in line:
                    # Handle different OCR variations
                    if "Данс:" in line:
                        parts = line.split("Данс:")
                    elif "AДcаcнoсu:nt:" in line:
                        parts = line.split("AДcаcнoсu:nt:")
                    elif "Account:" in line:
                        parts = line.split("Account:")

                    if len(parts) > 1:
                        # Extract account number, remove [MNT] suffix if present
                        account_part = parts[1].strip()
                        # Extract just the account number (digits before [MNT] or space)
                        import re

                        account_match = re.search(r"(\d+)", account_part)
                        if account_match:
                            account_number = account_match.group(1)
                            logger.info(
                                f"[GOLOMT] Found account number: '{account_number}'"
                            )
                elif "Харилцагчийн нэр:" in line:
                    parts = line.split("Харилцагчийн нэр:")
                    if len(parts) > 1:
                        customer_part = parts[1].strip()
                        # Remove extra info like (R000693755) and date range
                        import re

                        # Extract name before parentheses or extra info
                        name_match = re.match(r"^([А-ЯЁ\s]+)", customer_part)
                        if name_match:
                            customer_name = name_match.group(1).strip()
                        else:
                            customer_name = customer_part.split("(")[0].strip()
                        logger.info(f"[GOLOMT] Found customer name: '{customer_name}'")

    def _finalize(date_str, amt_str, tx_type, desc):
        row = [None] * 8
        row[0] = isValidDate(date_str, "%Y.%m.%d")
        amount_val = strToFloat(amt_str)
        if tx_type == "ОРЛОГО":
            row[4] = amount_val
        elif tx_type == "ЗАРЛАГА":
            row[3] = amount_val
        row[6] = desc.strip()
        rows.append(row)

    persisted_date: str | None = None

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp_path = Path(tmp.name)

    try:
        draw_golomt_on_pdf(pdf_path, tmp_path)

        with pdfplumber.open(str(tmp_path)) as pdf:
            for page_idx, page in enumerate(pdf.pages):
                crop = (
                    [20, 200, page.width, page.height]
                    if page_idx == 0
                    else [20, 30, page.width, page.height]
                )
                tables = page.crop(crop, strict=True).extract_tables(
                    {"vertical_strategy": "lines", "horizontal_strategy": "text"}
                )

                for table in tables:
                    for row in table:
                        row = [c.strip() if c else "" for c in row]
                        if all(not c for c in row):
                            continue

                        maybe_date = row[0]
                        date_ok = isValidDate(maybe_date, "%Y.%m.%d")
                        tx_type = row[2] if len(row) > 2 else ""

                        if date_ok and tx_type == "":
                            persisted_date = maybe_date
                            continue

                        if tx_type in ["ОРЛОГО", "ЗАРЛАГА"]:
                            amt_str = row[1] if len(row) > 1 else ""
                            desc = " ".join(row[3:]) if len(row) > 3 else ""
                            _finalize(
                                maybe_date if date_ok else persisted_date,
                                amt_str,
                                tx_type,
                                desc,
                            )
    finally:
        tmp_path.unlink(missing_ok=True)

    logger.info(f"[GOLOMT] Extraction complete:")
    logger.info(f"[GOLOMT] - Rows found: {len(rows)}")
    logger.info(f"[GOLOMT] - Customer name: '{customer_name}'")
    logger.info(f"[GOLOMT] - Account number: '{account_number}'")

    return rows, "GOLOMT", customer_name, account_number


# ╭──────────────────────────────────────────────────────────╮
# │ State Bank (Хэвлэсэн … YYYY.)                            │
# ╰──────────────────────────────────────────────────────────╯
@register_bank(
    lambda w: len(w) > 2 and w[0] == "Хэвлэсэн" and len(w[2]) > 4 and w[2][4] == "."
)
def getStateData(pdf_path: str | Path) -> Tuple[List[List], str, str, str]:
    rows: list[list] = []
    customer_name = ""
    account_number = ""

    with pdfplumber.open(str(pdf_path)) as pdf:
        if pdf.pages:
            # Extract customer info from first page
            first_page_text = pdf.pages[0].extract_text() or ""
            lines = first_page_text.split("\n")

            for line in lines:
                if "Харилцагч:" in line:
                    parts = line.split("Харилцагч:")
                    if len(parts) > 1:
                        customer_name = parts[1].strip()
                elif "Дансны дугаар:" in line:
                    parts = line.split("Дансны дугаар:")
                    if len(parts) > 1:
                        account_number = parts[1].strip()

        for page_idx, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()
            for tbl in tables:
                for i, raw in enumerate(tbl):
                    if i == 0:
                        continue
                    date_str = f"{raw[0]} {raw[1]}"
                    try:
                        date = datetime.strptime(date_str, "%Y.%m.%d %H:%M")
                    except ValueError:
                        break
                    row = raw[:]  # copy
                    row[:2] = [date]  # ❷ *shrink* first two slots to 1
                    row[1] = row[2]  # branch
                    row[2] = None  # beginning_balance (not provided)

                    row = row[:-3]  # drop the summary columns at the end
                    row[4], row[5] = strToFloat(row[5]), strToFloat(row[4])
                    row[6] = strToFloat(row[6])
                    row[7] = row[7].replace("\n", "")

                    row.append(row[3])  # move description to the end
                    del row[3]
                    row[6], row[7] = row[7], row[6]  # swap ending_balance / description
                    rows.append(row)

    return rows, "STATE", customer_name, account_number


# ╭──────────────────────────────────────────────────────────╮
# │ TDB Bank                                                │
# ╰──────────────────────────────────────────────────────────╯
@register_bank(
    lambda w: len(w) > 2 and w[0] == "Хэвлэсэн" and len(w[2]) > 4 and w[2][4] == "/"
)
def getTDBData(pdf_path: str | Path) -> Tuple[List[List], str, str, str]:
    res: list[list] = []
    customer_name = ""
    account_number = ""

    # Extract customer info from first page
    with pdfplumber.open(str(pdf_path)) as pdf_initial:
        if pdf_initial.pages:
            first_page_text = pdf_initial.pages[0].extract_text() or ""
            lines = first_page_text.split("\n")

            for line in lines:
                # TDB might have different field names, adjust as needed
                if "Харилцагч:" in line or "Нэр:" in line:
                    parts = line.split(":")
                    if len(parts) > 1:
                        customer_name = parts[1].strip()
                elif "Данс:" in line or "Дансны дугаар:" in line:
                    parts = line.split(":")
                    if len(parts) > 1:
                        account_number = parts[1].strip()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp_path = Path(tmp.name)

    try:
        draw_tdb_on_pdf(pdf_path, tmp_path)

        with pdfplumber.open(str(tmp_path)) as pdf:
            for idx, page in enumerate(pdf.pages):
                crop = (
                    [10, 160, page.width, page.height - 10]
                    if idx == 0
                    else [
                        10,
                        35,
                        page.width,
                        page.height - 10,
                    ]
                )
                tables = page.crop(crop, strict=True).extract_tables()
                for tbl in tables:
                    for raw in tbl:
                        if isValidDate(f"{raw[0]} {raw[1]}", "%Y.%m.%d %I:%M:%S%p"):
                            row = [None] * 8
                            row[0] = isValidDate(
                                f"{raw[0]} {raw[1]}", "%Y.%m.%d %I:%M:%S%p"
                            )
                            row[1] = raw[2]
                            row[4] = strToFloat(raw[3])
                            row[3] = strToFloat(raw[4])
                            row[7] = raw[6]
                            row[6] = raw[9]
                            row[5] = strToFloat(raw[8])
                            res.append(row)
    finally:
        tmp_path.unlink(missing_ok=True)

    return res, "TDB", customer_name, account_number


# ╭──────────────────────────────────────────────────────────╮
# │ Khas Bank                                               │
# ╰──────────────────────────────────────────────────────────╯
@register_bank(lambda w: bool(w) and w[0] == "ДАНСНЫ")
def getKhasData(pdf_path: str | Path) -> Tuple[List[List], str, str, str]:
    rows: list[list] = []
    customer_name = ""
    account_number = ""

    with pdfplumber.open(str(pdf_path)) as pdf:
        if pdf.pages:
            # Extract customer info from first page
            first_page_text = pdf.pages[0].extract_text() or ""
            lines = first_page_text.split("\n")

            for line in lines:
                if "Үндсэн эзэмшигч:" in line:
                    parts = line.split("Үндсэн эзэмшигч:")
                    if len(parts) > 1:
                        customer_part = parts[1].strip()
                        # Remove extra info like "Нийт орлого: 810,381,688.00"
                        if "Нийт орлого:" in customer_part:
                            customer_name = customer_part.split("Нийт орлого:")[
                                0
                            ].strip()
                        else:
                            customer_name = customer_part
                elif "Дансны дугаар:" in line or "Дансны дугаар :" in line:
                    if "Дансны дугаар:" in line:
                        parts = line.split("Дансны дугаар:")
                    else:
                        parts = line.split("Дансны дугаар :")
                    if len(parts) > 1:
                        account_number = parts[1].strip()

        for page in pdf.pages:
            for tbl in page.extract_tables():
                for raw in tbl:
                    if (raw[5] or raw[4]) and isValidDate(raw[0], "%Y-%m-%d"):
                        row = [None] * 8
                        row[0] = isValidDate(raw[0], "%Y-%m-%d")
                        row[3] = 0 if raw[5] == "-" else strToFloat(raw[5])
                        row[4] = 0 if raw[4] == "-" else strToFloat(raw[4])
                        row[5] = strToFloat(raw[6])
                        row[6] = raw[1]
                        row[7] = "".join(re.findall(r"\\d+", raw[2]))
                        rows.append(row)

    return rows, "KHAS", customer_name, account_number


# ────────────────────────────────────────────────────────────
# public façade (back‑compat)
# ────────────────────────────────────────────────────────────
def getBank(filename: str):
    """
    Legacy entry‑point kept for the rest of the codebase.
    Internally delegates to the registry’s detect_bank().
    """
    return detect_bank(filename)
