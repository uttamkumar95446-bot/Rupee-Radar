"""Basic PDF text and table extraction for bank statement PDFs.

Supports digitally-generated PDFs with extractable text.
For scanned/image-based PDFs, returns a fallback message.
"""

import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path: str) -> str:
    """Extract raw text from a digitally-generated PDF.

    Args:
        file_path: Path to the PDF file.

    Returns:
        Extracted text content.

    Raises:
        ValueError: If the PDF is password-protected or cannot be read.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise ImportError("PyMuPDF is required for PDF extraction. Install: pip install pymupdf")

    try:
        doc = fitz.open(file_path)
    except Exception as e:
        error_msg = str(e).lower()
        if "password" in error_msg:
            raise ValueError("PDF is password-protected. Please upload an unprotected file.")
        raise ValueError(f"Unable to read PDF file: {e}")

    if doc.is_encrypted:
        doc.close()
        raise ValueError("PDF is password-protected. Please upload an unprotected file.")

    text_parts = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        page_text = page.get_text()

        if page_text.strip():
            text_parts.append(f"--- Page {page_num + 1} ---\n{page_text}")
        else:
            logger.warning(f"Page {page_num + 1} has no extractable text (may be a scanned image).")
            text_parts.append(f"--- Page {page_num + 1} ---\n[No text layer found - may contain table data]")

    doc.close()

    if not text_parts:
        raise ValueError("No text could be extracted from the PDF. It may be a scanned image.")

    return "\n\n".join(text_parts)


def extract_tables_from_pdf(file_path: str) -> List[List[str]]:
    """Attempt to extract tabular data from a PDF using Camelot.

    Args:
        file_path: Path to the PDF file.

    Returns:
        List of text lines extracted from PDF tables, or empty list if Camelot fails.
    """
    try:
        import camelot
    except ImportError:
        logger.warning("Camelot not installed. Skipping table extraction.")
        return []

    try:
        tables = camelot.read_pdf(file_path, pages="all", flavor="lattice")
        if tables.n == 0:
            tables = camelot.read_pdf(file_path, pages="all", flavor="stream")
    except Exception as e:
        logger.warning(f"Camelot table extraction failed: {e}")
        return []

    lines = []
    for table in tables:
        for row in table.df.values:
            line = "|".join(str(cell).strip() for cell in row)
            if line.strip():
                lines.append(line)

    return lines
