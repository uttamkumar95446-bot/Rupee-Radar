"""Input validation utilities for file uploads and data processing."""

import os
from typing import List, Tuple

from backend.core.config import settings


def validate_file_extension(filename: str) -> Tuple[bool, str]:
    """Check if the file has an allowed extension."""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        return False, (
            f"Unsupported file format '{ext}'. "
            f"Allowed formats: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    return True, ""


def validate_file_size(file_size: int) -> Tuple[bool, str]:
    """Check if the file size is within the allowed limit."""
    if file_size == 0:
        return False, "The uploaded file is empty."
    if file_size > settings.MAX_UPLOAD_SIZE_BYTES:
        return False, (
            f"File size exceeds the maximum limit of "
            f"{settings.MAX_UPLOAD_SIZE_MB} MB."
        )
    return True, ""


def validate_job_id(job_id: str) -> Tuple[bool, str]:
    """Basic validation that job_id looks like a UUID."""
    import re
    pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    if not re.match(pattern, job_id, re.IGNORECASE):
        return False, "Invalid job ID format."
    return True, ""


def validate_transaction_data(transactions: List[dict]) -> List[str]:
    """Validate a list of raw parsed transactions and return warnings."""
    warnings = []
    for i, txn in enumerate(transactions):
        if txn.get("amount") is None or txn["amount"] == 0:
            warnings.append(f"Row {txn.get('row_number', i + 1)}: Missing or zero amount.")
        if not txn.get("date"):
            warnings.append(f"Row {txn.get('row_number', i + 1)}: Missing date.")
    return warnings
