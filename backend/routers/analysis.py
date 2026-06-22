"""Analysis polling router — returns job status, results, and manual overrides."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status

from backend.core.categories import ALL_CATEGORIES
from backend.models.schemas import AnalysisResponse, JobStatus
from backend.routers.upload import get_job
from backend.utils.validators import validate_job_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Analysis"])


@router.get(
    "/analysis/{job_id}",
    response_model=JobStatus,
    summary="Get analysis results",
    description="Poll for the results of a previously uploaded bank statement analysis.",
)
async def get_analysis(job_id: str):
    """Get the status and results of an analysis job.

    - While processing: returns {"status": "processing", "data": null}
    - When completed: returns {"status": "completed", "data": AnalysisResponse}
    - On failure: returns {"status": "failed", "error": "error message"}
    """
    is_valid, error_msg = validate_job_id(job_id)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg,
        )

    job = get_job(job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis job not found.",
        )

    if job["status"] == "processing":
        return JobStatus(status="processing", data=None)

    if job["status"] == "failed":
        return JobStatus(
            status="failed",
            data=None,
            error=job.get("error", "Unknown error occurred during processing."),
        )

    data_dict = job.get("data")
    if data_dict:
        analysis = AnalysisResponse.model_validate(data_dict)
        return JobStatus(status="completed", data=analysis)

    return JobStatus(
        status="failed",
        data=None,
        error="Analysis completed but no data found.",
    )


@router.put(
    "/analysis/{job_id}/transactions/{transaction_id}/category",
    summary="Override transaction category",
    description="Manually override the category for a specific transaction.",
)
async def override_category(
    job_id: str,
    transaction_id: str,
    category: str = Query(..., description="New category: Food, Travel, Shopping, Bills, EMI, Subscriptions, Salary, Rent, Investments, Other"),
):
    """Manually override the category of a transaction.

    Args:
        job_id: Analysis job ID.
        transaction_id: Transaction UUID.
        category: New category value.
    """
    is_valid, error_msg = validate_job_id(job_id)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis job not found.")
    if job["status"] != "completed":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Analysis is not yet completed.")

    data_dict = job.get("data")
    if not data_dict:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No data found for this job.")

    # Validate category
    if category not in ALL_CATEGORIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid category '{category}'. Must be one of: {', '.join(ALL_CATEGORIES)}",
        )

    # Find and update the transaction
    transactions = data_dict.get("transactions", [])
    updated = False
    for txn in transactions:
        if txn.get("id") == transaction_id:
            old_cat = txn.get("category", "Unknown")
            txn["category"] = category
            txn["category_confidence"] = 1.0  # Manual override = max confidence
            updated = True
            logger.info(f"Category override: {transaction_id}: {old_cat} -> {category}")
            break

    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found.")

    return {"status": "ok", "message": f"Transaction category updated to '{category}'."}


@router.put(
    "/analysis/{job_id}/transactions/{transaction_id}/recurring",
    summary="Override recurring flag",
    description="Manually set or clear the recurring flag on a transaction.",
)
async def override_recurring(
    job_id: str,
    transaction_id: str,
    is_recurring: bool = Query(..., description="Set to true to mark as recurring"),
    recurring_type: Optional[str] = Query(None, description="Type: subscription, emi, rent, sip, insurance"),
):
    """Manually override the recurring flag on a transaction."""
    is_valid, error_msg = validate_job_id(job_id)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis job not found.")
    if job["status"] != "completed":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Analysis is not yet completed.")

    data_dict = job.get("data")
    if not data_dict:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No data found for this job.")

    if is_recurring and recurring_type:
        valid_types = ["subscription", "emi", "rent", "sip", "insurance"]
        if recurring_type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid recurring type '{recurring_type}'. Must be one of: {', '.join(valid_types)}",
            )

    # Find and update the transaction
    transactions = data_dict.get("transactions", [])
    updated = False
    for txn in transactions:
        if txn.get("id") == transaction_id:
            txn["is_recurring"] = is_recurring
            txn["recurring_type"] = recurring_type if is_recurring else None
            updated = True
            logger.info(f"Recurring override: {transaction_id}: recurring={is_recurring}, type={recurring_type}")
            break

    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found.")

    msg = f"Transaction recurring flag set to '{is_recurring}'."
    if is_recurring and recurring_type:
        msg += f" Type: {recurring_type}."
    return {"status": "ok", "message": msg}
