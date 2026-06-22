"""Transaction cleaning, normalization, deduplication, and balance validation."""

import hashlib
import logging
import re
import uuid
from datetime import date, datetime
from typing import Dict, List, Optional, Set, Tuple

from backend.core.categories import DECLINED_KEYWORDS, TRANSFER_KEYWORDS
from backend.models.schemas import RawTransaction, Transaction

logger = logging.getLogger(__name__)


def generate_transaction_hash(txn: RawTransaction) -> str:
    """Generate a unique hash for a transaction for deduplication.

    Uses date + description + amount + type.
    """
    raw = f"{txn.date}|{txn.description}|{txn.amount}|{txn.txn_type}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def normalize_merchant(description: str) -> Tuple[str, Optional[str]]:
    """Extract a clean merchant name from a transaction description.

    Handles patterns like:
    - "Swiggy*12345" → "Swiggy"
    - "AMZN MKTPLC IN" → "Amazon"
    - "UPI/GOOGLEPAY/abc@paytm" → "Google Pay"

    Returns:
        Tuple of (cleaned_description, merchant_name)
    """
    if not description:
        return description, None

    original = description
    desc = description.strip()

    # Remove UPI transaction IDs
    upi_pattern = re.compile(
        r"(?:UPI|UPI/|upi/)?"
        r"(?:[0-9]+\-)?"
        r"(?:[A-Za-z0-9._%+-]+@[A-Za-z]+)",
        re.IGNORECASE
    )
    desc = upi_pattern.sub("", desc).strip()

    # Remove common suffixes: *numbers, -numbers, /numbers
    desc = re.sub(r"[\*\#\-\/]\d{3,}$", "", desc).strip()

    # Remove parenthetical codes: (ABC123), [XYZ]
    desc = re.sub(r"[\(\[][A-Z0-9]+[\)\]]", "", desc).strip()

    # Remove trailing location/merchant codes
    desc = re.sub(r"\s+(IN|MUM|DEL|BLR|HYD|CHE|KOL|PUN|IND|DL|MH|KN|TN)\s*$", "", desc, flags=re.IGNORECASE).strip()

    # Remove special characters at start/end
    desc = desc.strip("*#- ")

    # Try to extract merchant name from common patterns
    merchant = None

    # Known merchant patterns
    known_merchants = {
        "swiggy": "Swiggy",
        "zomato": "Zomato",
        "amazon": "Amazon",
        "flipkart": "Flipkart",
        "myntra": "Myntra",
        "netflix": "Netflix",
        "uber": "Uber",
        "ola": "Ola",
        "airtel": "Airtel",
        "jio": "Jio",
        "vi ": "Vi",
        "vodafone": "Vodafone",
        "idea": "Idea",
        "google": "Google",
        "microsoft": "Microsoft",
        "apple": "Apple",
        "spotify": "Spotify",
        "hotstar": "Hotstar",
        "prime video": "Prime Video",
        "makemytrip": "MakeMyTrip",
        "goibibo": "Goibibo",
        "irctc": "IRCTC",
        "redbus": "RedBus",
        "paytm": "Paytm",
        "phonepe": "PhonePe",
        "gpay": "Google Pay",
        "razorpay": "Razorpay",
        "bigbasket": "BigBasket",
        "dmart": "DMart",
        "reliance": "Reliance",
        "tatasky": "Tata Sky",
        "tata": "Tata",
        "zepto": "Zepto",
        "blinkit": "Blinkit",
        "instamart": "Instamart",
        "jiomart": "JioMart",
    }

    desc_lower = desc.lower()
    for keyword, merchant_name in known_merchants.items():
        if keyword in desc_lower:
            merchant = merchant_name
            break

    # If no merchant found, use first word as merchant name
    if merchant is None and desc:
        first_word = desc.split()[0]
        if len(first_word) > 2 and not first_word.isdigit():
            merchant = first_word.strip("*#-")

    # Clean up multiple spaces
    cleaned = re.sub(r"\s+", " ", desc).strip()

    # If cleaning removed everything, keep original
    if not cleaned:
        cleaned = original.strip()

    # If no merchant name could be extracted, leave as None
    return cleaned, merchant


def is_transfer(description: str) -> bool:
    """Check if a transaction description indicates a transfer."""
    desc_lower = description.lower()
    return any(kw in desc_lower for kw in TRANSFER_KEYWORDS)


def is_declined(description: str) -> bool:
    """Check if a transaction description indicates a failed/declined transaction."""
    desc_lower = description.lower()
    return any(kw in desc_lower for kw in DECLINED_KEYWORDS)


def is_future_date(txn_date: date) -> bool:
    """Check if a transaction date is in the future."""
    return txn_date > date.today()


def clean_transactions(
    raw_transactions: List[RawTransaction],
    source_file: str = "",
) -> Tuple[List[Transaction], List[str]]:
    """Clean, normalize, and deduplicate raw parsed transactions.

    Args:
        raw_transactions: List of raw transactions from the parser.
        source_file: Name of the source file for traceability.

    Returns:
        Tuple of (cleaned_transactions, warnings).
    """
    cleaned: List[Transaction] = []
    warnings: List[str] = []
    seen_hashes: Set[str] = set()

    # Sort by date then row number
    raw_sorted = sorted(
        [t for t in raw_transactions if t.date is not None],
        key=lambda t: (t.date, t.row_number),
    )

    # Handle transactions with no date separately
    no_date_txns = [t for t in raw_transactions if t.date is None]
    if no_date_txns:
        warnings.append(f"{len(no_date_txns)} transaction(s) have no valid date and were skipped.")

    for raw in raw_sorted:
        txn_warnings: List[str] = []

        # Skip declined/failed transactions
        if is_declined(raw.description):
            warnings.append(f"Row {raw.row_number}: Skipped declined/failed transaction: '{raw.description[:50]}'")
            continue

        # Normalize description and extract merchant
        clean_desc, merchant = normalize_merchant(raw.description)

        # Generate hash and deduplicate
        txn_hash = generate_transaction_hash(raw)
        if txn_hash in seen_hashes:
            warnings.append(f"Row {raw.row_number}: Duplicate transaction skipped (matches row with same date/description/amount).")
            continue
        seen_hashes.add(txn_hash)

        # Flag suspicious entries
        is_suspicious = False
        suspicious_reason = None

        if raw.amount is None or raw.amount <= 0:
            continue

        # Detect and mark transfers
        if is_transfer(raw.description):
            txn_warnings.append("Transfer between accounts detected.")

        # Flag future dates
        if is_future_date(raw.date):
            is_suspicious = True
            suspicious_reason = "Transaction date is in the future."
            txn_warnings.append(suspicious_reason)

        # Build cleaned transaction with unique ID
        txn = Transaction(
            id=str(uuid.uuid4()),
            date=raw.date,
            description=clean_desc,
            original_description=raw.description,
            amount=raw.amount,
            txn_type=raw.txn_type or "debit",
            merchant=merchant,
            is_suspicious=is_suspicious,
            suspicious_reason=suspicious_reason,
        )

        if txn_warnings:
            warnings.extend(txn_warnings)

        cleaned.append(txn)

    if len(cleaned) < len(raw_transactions):
        warnings.append(
            f"Cleaned {len(cleaned)}/{len(raw_transactions)} transactions "
            f"({len(raw_transactions) - len(cleaned)} skipped)."
        )

    logger.info(f"Cleaning complete: {len(cleaned)} valid transactions from {len(raw_transactions)} raw.")
    return cleaned, warnings


def validate_balance(
    transactions: List[Transaction],
    opening_balance: Optional[float] = None,
    closing_balance: Optional[float] = None,
    tolerance: float = 0.50,
) -> Tuple[bool, Optional[str]]:
    """Validate the Golden Rule: Opening + Credits - Debits ≈ Closing.

    Args:
        transactions: List of cleaned transactions.
        opening_balance: Opening balance from statement (if available).
        closing_balance: Closing balance from statement (if available).
        tolerance: Accepted rounding tolerance in currency units.

    Returns:
        Tuple of (is_valid, message).
    """
    if opening_balance is None or closing_balance is None:
        return False, "Opening or closing balance not available. Balance validation skipped."

    total_credits = sum(t.amount for t in transactions if t.txn_type == "credit")
    total_debits = sum(t.amount for t in transactions if t.txn_type == "debit")

    expected_closing = opening_balance + total_credits - total_debits
    difference = abs(expected_closing - closing_balance)

    if difference <= tolerance:
        return True, (
            f"Balance validated ✓ (Opening: ₹{opening_balance:,.2f}, "
            f"Credits: ₹{total_credits:,.2f}, Debits: ₹{total_debits:,.2f}, "
            f"Closing: ₹{closing_balance:,.2f})"
        )
    else:
        return False, (
            f"Balance mismatch! Expected closing: ₹{expected_closing:,.2f}, "
            f"Actual closing: ₹{closing_balance:,.2f}, "
            f"Difference: ₹{difference:,.2f}"
        )
