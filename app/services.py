"""
Business logic for bulk certificate processing.

process_job() is called as a FastAPI BackgroundTask — it runs after the
HTTP response is sent, so the client gets an immediate 202 and can poll
GET /jobs/{job_id} for progress.

Why BackgroundTasks instead of Celery/Redis?
  - Simple to set up — no external services required
  - Keeps the API responsive (response returns before processing starts)
  - Demonstrates asynchronous background processing clearly
  - For production-scale workloads a proper queue (Celery, RQ, etc.) would
    be more appropriate for reliability, retries, and horizontal scaling.
"""

import os
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import GenerationJob, Certificate
from app.certificate import generate_certificate


# Directory where generated PDFs are stored (relative, works cross-platform)
GENERATED_DIR = os.path.join(os.path.dirname(__file__), "..", "generated")


def process_job(job_id: int, db: Session) -> None:
    """
    Background task: generate PDF certificates for every recipient in a job.

    Processing rules:
      - Mark job as 'processing' before starting.
      - Attempt PDF generation for each certificate independently.
      - On success  → mark certificate 'success', increment job.successful.
      - On failure  → mark certificate 'failed', store error, increment job.failed.
      - One failure does NOT stop remaining certificates.
      - After all certificates are processed, set final job status:
          all succeeded      → 'completed'
          some failed        → 'completed_with_errors'
          all failed         → 'failed'
    """
    job: GenerationJob = db.get(GenerationJob, job_id)
    if job is None:
        return  # nothing to do — shouldn't happen in normal flow

    # Mark job as in-progress
    job.status = "processing"
    db.commit()

    certificates = (
        db.query(Certificate)
        .filter(Certificate.job_id == job_id)
        .all()
    )

    for cert in certificates:
        _process_single_certificate(cert, job, db)

    # Determine final job status
    if job.failed == 0:
        job.status = "completed"
    elif job.successful == 0:
        job.status = "failed"
    else:
        job.status = "completed_with_errors"

    job.completed_at = datetime.now(timezone.utc)
    db.commit()


def _process_single_certificate(
    cert: Certificate,
    job: GenerationJob,
    db: Session,
) -> None:
    """
    Generate PDF for one certificate record.
    Updates the certificate and job counters in-place, then commits.
    """
    output_path = _build_output_path(job.id, cert.certificate_id)

    try:
        generate_certificate(
            recipient_name=cert.recipient_name,
            recipient_email=cert.recipient_email,
            certificate_id=cert.certificate_id,
            event_name=job.event_name,
            event_date=job.event_date,
            output_path=output_path,
        )
        cert.status = "success"
        cert.file_path = output_path
        job.successful += 1

    except Exception as e:
        # Failure is isolated — we record the error and move on
        cert.status = "failed"
        cert.error_message = str(e)
        job.failed += 1

    db.commit()


def _build_output_path(job_id: int, certificate_id: str) -> str:
    """Return the full file path for a generated PDF."""
    # Sanitize certificate_id so it's safe as a filename
    safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in certificate_id)
    filename = f"job_{job_id}_{safe_id}.pdf"
    return os.path.abspath(os.path.join(GENERATED_DIR, filename))
