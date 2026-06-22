"""File upload router — accepts CSV/PDF bank statements and starts async processing."""

import logging
import os
import uuid
from datetime import datetime

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from backend.core.config import settings
from backend.models.schemas import AnalysisResponse, RawTransaction, UploadResponse
from backend.services.categorizer import categorize_transactions
from backend.services.cleaner import clean_transactions, validate_balance
from backend.services.insights import generate_insights
from backend.services.metrics import compute_metrics
from backend.services.parser import parse_csv
from backend.services.recurring_detector import detect_recurring_payments
from backend.utils.pdf_extractor import extract_text_from_pdf, extract_tables_from_pdf
from backend.utils.validators import validate_file_extension, validate_file_size

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Upload"])

# In-memory job store
# job_id -> { status, data, error, created_at }
job_store: dict = {}


def get_job(job_id: str) -> dict | None:
    """Get a job from the in-memory store by ID."""
    return job_store.get(job_id)


def set_job(job_id: str, data: dict):
    """Update a job in the in-memory store."""
    job_store[job_id] = data


async def process_file(job_id: str, file_path: str, filename: str):
    """Background task: parse, clean, compute metrics, store results.

    Args:
        job_id: Unique job identifier.
        file_path: Path to the uploaded file on disk.
        filename: Original filename for display.
    """
    try:
        ext = os.path.splitext(filename)[1].lower()
        raw_transactions = []
        warnings = []

        if ext == ".csv":
            raw_transactions = parse_csv(file_path)
        elif ext == ".pdf":
            text = extract_text_from_pdf(file_path)
            tables = extract_tables_from_pdf(file_path)
            # For Phase 1, basic PDF support extracts text lines
            # Full PDF parsing will be enhanced in later phases
            warnings.append("PDF parsing is basic in Phase 1. Column detection may be inaccurate.")
            # Simple line-based extraction as fallback
            raw_transactions = []
            for idx, line in enumerate(text.split("\n")):
                line = line.strip()
                if line and not line.startswith("---"):
                    raw_transactions.append(
                        RawTransaction(
                            description=line,
                            original_line=line,
                            row_number=idx + 1,
                        )
                    )
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file format: {ext}")

        # Clean transactions
        cleaned_txns, clean_warnings = clean_transactions(raw_transactions, source_file=filename)
        warnings.extend(clean_warnings)

        # ── Phase 2: Categorize transactions ──
        # Check if any AI provider is configured
        provider = settings.LLM_PROVIDER
        llm_available = (
            (provider == "groq" and bool(settings.GROQ_API_KEY)) or
            (provider == "openai" and bool(settings.OPENAI_API_KEY)) or
            (provider == "local")
        )
        force_rules = not llm_available
        categorized_txns, cat_warnings = categorize_transactions(
            cleaned_txns,
            force_rules_only=force_rules,
        )
        warnings.extend(cat_warnings)

        # ── Phase 2: Detect recurring payments ──
        recurring_payments, rec_warnings = detect_recurring_payments(categorized_txns)
        warnings.extend(rec_warnings)

        # Compute metrics (now with categories)
        metrics = compute_metrics(categorized_txns)

        # ── Phase 3: Generate AI insights ──
        insights, ins_warnings = generate_insights(
            metrics,
            recurring_payments,
            categorized_txns,
            force_rules_only=force_rules,
        )
        warnings.extend(ins_warnings)

        # Balance validation
        balance_verified = False

        # Build response
        analysis = AnalysisResponse(
            file_name=filename,
            parsed_at=datetime.utcnow(),
            transactions=categorized_txns,
            total_transactions=len(categorized_txns),
            recurring_payments=recurring_payments,
            metrics=metrics,
            insights=insights,
            warnings=warnings,
            total_parsed=len(raw_transactions),
            total_skipped=len(raw_transactions) - len(categorized_txns),
            balance_verified=balance_verified,
        )

        set_job(job_id, {
            "status": "completed",
            "data": analysis.model_dump(mode="json"),
            "error": None,
            "created_at": datetime.utcnow().isoformat(),
        })

        logger.info(f"Job {job_id} completed: {len(cleaned_txns)} transactions processed.")

        # Clean up uploaded file
        try:
            os.remove(file_path)
        except OSError:
            logger.warning(f"Could not remove temporary file: {file_path}")

    except Exception as e:
        logger.exception(f"Job {job_id} failed: {e}")
        set_job(job_id, {
            "status": "failed",
            "data": None,
            "error": str(e),
            "created_at": datetime.utcnow().isoformat(),
        })


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload a bank statement file",
    description="Accepts CSV or PDF bank statement files. Returns a job_id for polling results.",
)
async def upload_file(file: UploadFile = File(...)):
    """Upload a bank statement CSV or PDF for processing.

    Returns a 202 Accepted with a job_id that can be polled via GET /api/analysis/{job_id}.
    """
    # Validate file extension
    is_valid, error_msg = validate_file_extension(file.filename or "")
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

    # Validate file content size
    content = await file.read()
    is_valid, error_msg = validate_file_size(len(content))
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

    # Generate unique job ID
    job_id = str(uuid.uuid4())

    # Save uploaded file temporarily
    upload_dir = os.path.join(settings.BASE_DIR, settings.UPLOAD_DIR)
    os.makedirs(upload_dir, exist_ok=True)
    temp_path = os.path.join(upload_dir, f"{job_id}_{file.filename}")

    try:
        with open(temp_path, "wb") as f:
            f.write(content)
    except OSError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not save uploaded file: {e}",
        )

    # Initialize job in store
    set_job(job_id, {
        "status": "processing",
        "data": None,
        "error": None,
        "created_at": datetime.utcnow().isoformat(),
    })

    # Start background processing
    import asyncio
    asyncio.create_task(process_file(job_id, temp_path, file.filename or "unknown"))

    logger.info(f"Upload accepted: job_id={job_id}, file={file.filename}")

    return UploadResponse(
        job_id=job_id,
        status="processing",
        message="File received. Analysis in progress.",
    )
