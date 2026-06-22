"""Report generation router — generates downloadable HTML/PDF reports.

Phase 3: Full Jinja2 template rendering with Chart.js visualizations,
AI insights, recurring payments, and transaction log.
"""

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import HTMLResponse, Response
from jinja2 import Environment, FileSystemLoader, select_autoescape

from backend.routers.upload import get_job
from backend.utils.validators import validate_job_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Report"])

# Set up Jinja2 environment directly (not via Starlette's TemplateResponse)
# Using standalone Jinja2 avoids hashability issues with Starlette's template cache
templates_dir = Path(__file__).resolve().parent.parent / "templates"
jinja_env = Environment(
    loader=FileSystemLoader(str(templates_dir)),
    autoescape=select_autoescape(["html", "xml"]),
)

# Cached PDF availability check — tested once at module load
_pdf_available: bool | None = None


def _check_pdf_available() -> bool:
    """Check once (and cache) if PDF generation is available on this system.

    WeasyPrint requires system libraries (GTK, Pango, etc.) that
    may not be installed on all systems, especially Windows.
    Cached so we only test once per server session.

    Returns:
        True if PDF generation is available, False otherwise.
    """
    global _pdf_available
    if _pdf_available is None:
        try:
            from weasyprint import HTML as WeasyprintHTML
            WeasyprintHTML(string="<p>test</p>").write_pdf()
            _pdf_available = True
            logger.info("PDF generation: available (WeasyPrint works)")
        except Exception:
            _pdf_available = False
            logger.warning(
                "PDF generation: unavailable. WeasyPrint system libraries "
                "(GTK, Pango) not found. HTML reports will work fine."
            )
    return _pdf_available


@router.get(
    "/report/{job_id}",
    summary="Download analysis report",
    description="Generate and download an HTML or PDF report of the analysis.",
)
async def get_report(
    job_id: str,
    format: str = Query("html", description="Report format: 'pdf' or 'html'"),
):
    """Download a report of the analysis results.

    Supports HTML (interactive with Chart.js) and PDF (print-ready).
    """
    # Validate job_id
    is_valid, error_msg = validate_job_id(job_id)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg,
        )

    # Validate format
    if format not in ("pdf", "html"):
        format = "html"

    # Check job exists
    job = get_job(job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis job not found.",
        )

    if job["status"] == "processing":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Analysis still in progress. Please wait.",
        )

    if job["status"] == "failed":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Analysis failed: {job.get('error', 'Unknown error')}",
        )

    data_dict = job.get("data")
    if not data_dict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No analysis data found for this job.",
        )

    template_context = {
        "file_name": data_dict.get("file_name", "Unknown"),
        "parsed_at": data_dict.get("parsed_at", ""),
        "transactions": data_dict.get("transactions", []),
        "recurring_payments": data_dict.get("recurring_payments", []),
        "metrics": data_dict.get("metrics", {}),
        "insights": data_dict.get("insights", []),
        "total_transactions": data_dict.get("total_transactions", 0),
        "total_parsed": data_dict.get("total_parsed", 0),
        "total_skipped": data_dict.get("total_skipped", 0),
        "balance_verified": data_dict.get("balance_verified", False),
        "warnings": data_dict.get("warnings", []),
    }

    # Render the HTML template directly via Jinja2
    template = jinja_env.get_template("report.html")
    html_str = template.render(**template_context)

    if format == "pdf":
        # Check if weasyprint is available upfront
        pdf_available = _check_pdf_available()
        if not pdf_available:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail=(
                    "PDF generation is not available on this system. "
                    "Please use the HTML format instead. "
                    "To enable PDF, install WeasyPrint system dependencies: "
                    "https://doc.courtbouillon.org/weasyprint/stable/first_steps.html"
                ),
            )
        try:
            pdf_bytes = _html_to_pdf(html_str)
            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": (
                        f'attachment; filename="rupeeradar-report-{job_id[:8]}.pdf"'
                    )
                },
            )
        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"PDF generation failed: {e}. Please use the HTML format instead.",
            )

    return HTMLResponse(
        content=html_str,
        status_code=200,
        headers={
            "Content-Disposition": (
                f'inline; filename="rupeeradar-report-{job_id[:8]}.html"'
            )
        },
    )


def _html_to_pdf(html_str: str) -> bytes:
    """Convert an HTML string to PDF bytes using WeasyPrint.

    Args:
        html_str: Complete HTML document as a string.

    Returns:
        PDF content as bytes.

    Raises:
        RuntimeError: If PDF generation fails.
    """
    from weasyprint import HTML as WeasyprintHTML

    try:
        return WeasyprintHTML(string=html_str).write_pdf()
    except Exception as e:
        raise RuntimeError(f"Failed to generate PDF: {e}") from e
