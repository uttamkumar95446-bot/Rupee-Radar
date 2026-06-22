"""CSV parser for Indian bank statement formats.

Supports auto-detection of column mappings for HDFC, ICICI, SBI, Axis, and other
common Indian bank CSV formats. Normalizes dates, amounts, and debit/credit indicators.
"""

import csv
import io
import logging
import re
from datetime import date, datetime
from typing import Dict, List, Optional, Tuple

from backend.models.schemas import RawTransaction
from backend.core.categories import BANK_FORMAT_KEYWORDS

logger = logging.getLogger(__name__)

# Date format patterns to try, in order
DATE_FORMATS = [
    ("%d/%m/%Y", re.compile(r"^\d{2}/\d{2}/\d{4}$")),
    ("%m/%d/%Y", re.compile(r"^\d{2}/\d{2}/\d{4}$")),  # Ambiguous - will use as fallback
    ("%Y-%m-%d", re.compile(r"^\d{4}-\d{2}-\d{2}$")),
    ("%d-%m-%Y", re.compile(r"^\d{2}-\d{2}-\d{4}$")),
    ("%d-%b-%Y", re.compile(r"^\d{2}-[A-Za-z]{3}-\d{4}$")),
    ("%d/%m/%y", re.compile(r"^\d{2}/\d{2}/\d{2}$")),
    ("%d-%m-%y", re.compile(r"^\d{2}-\d{2}-\d{2}$")),
    ("%Y%m%d", re.compile(r"^\d{8}$")),
]

# Amount pattern: optional currency symbol, digits, optional comma/thousands, optional decimal
AMOUNT_PATTERN = re.compile(r"^[₹Rs.\s]*([-+]?[\d,]+(?:\.\d{1,2})?)\s*$")
AMOUNT_WITH_PARENS = re.compile(r"^\(([\d,]+(?:\.\d{1,2})?)\)$")  # (1234.56) = negative


class DateTimeEncoder:
    """Helper for parsing dates in various formats."""

    @staticmethod
    def parse_date(date_str: str) -> Optional[date]:
        """Try to parse a date string using multiple format patterns."""
        if not date_str or not isinstance(date_str, str):
            return None

        date_str = date_str.strip().strip('"').strip("'")

        for fmt, pattern in DATE_FORMATS:
            if pattern.match(date_str):
                try:
                    return datetime.strptime(date_str, fmt).date()
                except ValueError:
                    continue

        # Try pandas-style date parsing as fallback
        try:
            import pandas as pd
            parsed = pd.to_datetime(date_str, dayfirst=True, errors="coerce")
            if pd.notna(parsed):
                return parsed.date()
        except Exception:
            pass

        return None

    @staticmethod
    def parse_amount(amount_str: str) -> Optional[float]:
        """Parse a currency amount string to float."""
        if not amount_str or not isinstance(amount_str, str):
            return None

        amount_str = amount_str.strip().strip('"').strip("'")

        # Handle parenthetical negatives: (1,234.56) = -1234.56
        paren_match = AMOUNT_WITH_PARENS.match(amount_str)
        if paren_match:
            return -float(paren_match.group(1).replace(",", ""))

        # Strip currency symbols and whitespace
        amount_str = amount_str.replace("₹", "").replace("Rs", "").replace("$", "")
        amount_str = amount_str.replace(",", "").strip()

        try:
            return float(amount_str)
        except ValueError:
            return None


def detect_column_mapping(headers: List[str]) -> Dict[str, int]:
    """Auto-detect column indices based on header names.

    Returns a dict mapping canonical field names to column indices.
    """
    header_lower = [h.strip().lower() for h in headers]

    mapping = {}

    # Date column
    date_keywords = ["date", "txn date", "transaction date", "trans date", "value date",
                     "posting date", "dt", "dated"]
    for i, h in enumerate(header_lower):
        if any(kw in h for kw in date_keywords):
            mapping["date"] = i
            break

    # Description / narrative column
    desc_keywords = ["description", "narrative", "narration", "particulars", "particular", "details",
                     "trans details", "transaction details", "remarks", "note", "transaction"]
    for i, h in enumerate(header_lower):
        if any(kw in h for kw in desc_keywords) and "date" not in h:
            mapping["description"] = i
            break

    # Amount columns (use substring matching for headers like "Withdrawal (INR)")
    debit_keywords = ["debit", "dr", "withdrawal", "withdraw"]
    credit_keywords = ["credit", "cr", "deposit"]
    amount_keywords = ["amount", "amt"]
    for i, h in enumerate(header_lower):
        if any(kw in h for kw in debit_keywords):
            mapping["debit"] = i
            continue
        if any(kw in h for kw in credit_keywords):
            mapping["credit"] = i
            continue
        if any(kw in h for kw in amount_keywords):
            mapping["amount"] = i
            continue

    # Balance column
    balance_keywords = ["balance", "running balance", "closing balance", "available balance",
                        "bal", "closing bal"]
    for i, h in enumerate(header_lower):
        if any(kw in h for kw in balance_keywords):
            mapping["balance"] = i
            break

    # Chq/Ref number (optional)
    for i, h in enumerate(header_lower):
        if any(kw in h for kw in ["chq", "cheque", "ref no", "reference", "chq no"]):
            mapping["reference"] = i
            break

    return mapping


def parse_csv(file_path: str) -> List[RawTransaction]:
    """Parse a CSV bank statement file into RawTransaction objects.

    Uses auto-detection of column headers and handles multiple Indian bank formats.

    Args:
        file_path: Path to the CSV file.

    Returns:
        List of RawTransaction objects parsed from the file.

    Raises:
        ValueError: If the file cannot be parsed or contains no transactions.
    """
    rows = []
    detected_encoding = None

    # Try reading with different encodings
    encodings = ["utf-8", "utf-8-sig", "iso-8859-1", "cp1252", "latin-1"]
    csv_content = None

    for enc in encodings:
        try:
            with open(file_path, "r", encoding=enc) as f:
                csv_content = f.read()
            detected_encoding = enc
            break
        except (UnicodeDecodeError, UnicodeError):
            continue

    if csv_content is None:
        raise ValueError("Could not read the file. Unsupported encoding.")

    # Remove BOM if present
    if csv_content.startswith("\ufeff"):
        csv_content = csv_content[1:]

    # Try different delimiters
    delimiters = [",", ";", "\t", "|"]
    reader = None
    used_delimiter = None

    # Use csv.Sniffer to detect delimiter and dialect
    try:
        dialect = csv.Sniffer().sniff(csv_content[:1024])
        used_delimiter = dialect.delimiter
    except csv.Error:
        # Fallback: try common delimiters
        for delim in delimiters:
            if delim in csv_content[:512]:
                used_delimiter = delim
                break
        if not used_delimiter:
            used_delimiter = ","

    csv_reader = csv.reader(io.StringIO(csv_content), delimiter=used_delimiter)
    all_rows = list(csv_reader)

    if len(all_rows) < 2:
        raise ValueError("CSV file has no transaction data (need at least header + 1 row).")

    # Find header row (skip leading metadata rows)
    header_row_idx = 0
    for i, row in enumerate(all_rows):
        row_text = " ".join(str(cell).lower() for cell in row)
        if any(kw in row_text for kw in ["date", "description", "particulars", "narrative"]):
            header_row_idx = i
            break

    headers = [str(h).strip().strip('"').strip("'") for h in all_rows[header_row_idx]]
    column_map = detect_column_mapping(headers)

    if "date" not in column_map:
        logger.warning("No date column detected. Using column 0 as date.")
        column_map["date"] = 0
    if "description" not in column_map:
        logger.warning("No description column detected. Using column 1 as description.")
        column_map["description"] = min(1, len(headers) - 1)
    if "debit" not in column_map and "credit" not in column_map and "amount" not in column_map:
        raise ValueError(
            "Could not identify amount/debit/credit columns. "
            "Ensure the CSV has columns named: amount, debit, credit, or similar."
        )

    # Parse data rows
    skipped = 0
    for row_idx in range(header_row_idx + 1, len(all_rows)):
        row = all_rows[row_idx]
        if not row or all(cell.strip() == "" for cell in row):
            continue

        # Skip summary/total rows
        row_text = " ".join(str(cell).lower() for cell in row)
        if any(kw in row_text for kw in ["total", "subtotal", "balance", "opening", "closing",
                                          "grand total", "***", "---", "==="]):
            continue

        raw = RawTransaction(
            original_line=used_delimiter.join(row),
            row_number=row_idx + 1,
        )

        # Parse date
        date_idx = column_map.get("date")
        if date_idx is not None and date_idx < len(row):
            raw.date = DateTimeEncoder.parse_date(str(row[date_idx]))
        if raw.date is None:
            raw.warnings.append(f"Row {row_idx + 1}: Could not parse date '{row[date_idx] if date_idx is not None and date_idx < len(row) else ''}'.")

        # Parse description
        desc_idx = column_map.get("description")
        if desc_idx is not None and desc_idx < len(row):
            raw.description = str(row[desc_idx]).strip().strip('"').strip("'")

        # Parse amount (handle debit, credit, or generic amount columns)
        debit_idx = column_map.get("debit")
        credit_idx = column_map.get("credit")
        amount_idx = column_map.get("amount")

        if debit_idx is not None and credit_idx is not None:
            # Separate debit and credit columns
            debit_val = DateTimeEncoder.parse_amount(str(row[debit_idx])) if debit_idx < len(row) else None
            credit_val = DateTimeEncoder.parse_amount(str(row[credit_idx])) if credit_idx < len(row) else None

            if debit_val and debit_val != 0:
                raw.amount = abs(debit_val)
                raw.txn_type = "debit"
            elif credit_val and credit_val != 0:
                raw.amount = abs(credit_val)
                raw.txn_type = "credit"
        elif amount_idx is not None:
            # Single amount column with sign or "Dr"/"Cr" text
            amount_str = str(row[amount_idx]) if amount_idx < len(row) else ""
            amount_val = DateTimeEncoder.parse_amount(amount_str)

            if amount_val is not None and amount_val != 0:
                if amount_val < 0:
                    raw.amount = abs(amount_val)
                    raw.txn_type = "debit"
                else:
                    raw.amount = amount_val
                    # Check if description contains "Dr" or "Cr" hint
                    if any(cr_word in raw.description.lower() for cr_word in ["cr", "credit"]):
                        raw.txn_type = "credit"
                    elif any(dr_word in raw.description.lower() for dr_word in ["dr", "debit"]):
                        raw.txn_type = "debit"
                    else:
                        raw.txn_type = "credit"  # Assume credit if positive by default
        elif debit_idx is not None:
            val = DateTimeEncoder.parse_amount(str(row[debit_idx])) if debit_idx < len(row) else None
            if val and val != 0:
                raw.amount = abs(val)
                raw.txn_type = "debit"
        elif credit_idx is not None:
            val = DateTimeEncoder.parse_amount(str(row[credit_idx])) if credit_idx < len(row) else None
            if val and val != 0:
                raw.amount = abs(val)
                raw.txn_type = "credit"

        if raw.amount is None or raw.amount == 0:
            skipped += 1
            continue

        # Parse balance (optional)
        bal_idx = column_map.get("balance")
        if bal_idx is not None and bal_idx < len(row):
            raw.balance = DateTimeEncoder.parse_amount(str(row[bal_idx]))

        rows.append(raw)

    if len(rows) == 0:
        raise ValueError("No valid transactions found in the CSV file.")

    logger.info(
        f"Parsed {len(rows)} transactions from {file_path} "
        f"(skipped {skipped} rows, encoding={detected_encoding}, delimiter='{used_delimiter}')"
    )

    return rows
