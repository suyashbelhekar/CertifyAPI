"""
FastAPI application entry point.

Endpoints:
  POST   /jobs                               – create a bulk generation job
  GET    /jobs/{job_id}                      – check job status / progress
  GET    /jobs/{job_id}/certificates         – list certificate results for a job
  GET    /certificates/{job_id}/{cert_id}    – download a generated PDF
"""

import os
from datetime import datetime

from fastapi import FastAPI, Depends, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db, SessionLocal
from app.models import GenerationJob, Certificate
from app.schemas import (
    JobCreateRequest,
    JobCreateResponse,
    JobStatusResponse,
    CertificateResult,
    JobCertificatesResponse,
)
from app.services import process_job

# Create all tables on startup (safe to call multiple times)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Bulk Certificate Generator",
    description="Generate PDF certificates in bulk via a simple REST API.",
    version="1.0.0",
)


# ---------------------------------------------------------------------------
# POST /jobs
# ---------------------------------------------------------------------------

@app.post("/jobs", response_model=JobCreateResponse, status_code=202)
def create_job(
    payload: JobCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Create a new bulk certificate generation job.

    - Validates the request (Pydantic returns 422 on bad input automatically).
    - Persists the job and all certificate records.
    - Enqueues background processing immediately.
    - Returns 202 with job_id so the client can poll for progress.
    """
    # 1. Create the job record
    job = GenerationJob(
        event_name=payload.event_name,
        event_date=str(payload.event_date),   # store as "YYYY-MM-DD"
        status="queued",
        total=len(payload.recipients),
        successful=0,
        failed=0,
    )
    db.add(job)
    db.flush()  # assigns job.id without committing yet

    # 2. Create a Certificate record for every recipient
    for recipient in payload.recipients:
        cert = Certificate(
            job_id=job.id,
            certificate_id=recipient.certificate_id,
            recipient_name=recipient.name,
            recipient_email=str(recipient.email),
            status="pending",
        )
        db.add(cert)

    db.commit()
    db.refresh(job)

    # 3. Kick off background processing
    # We pass a fresh session factory so the background task has its own
    # database connection independent of the request session.
    bg_db = SessionLocal()
    background_tasks.add_task(_run_job_in_background, job.id, bg_db)

    return JobCreateResponse(
        job_id=job.id,
        status=job.status,
        total=job.total,
    )


def _run_job_in_background(job_id: int, db: Session) -> None:
    """Wrapper so the background task closes the session when done."""
    try:
        process_job(job_id, db)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# GET /jobs/{job_id}
# ---------------------------------------------------------------------------

@app.get("/jobs/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: int, db: Session = Depends(get_db)):
    """Return the current progress of a generation job."""
    job = db.get(GenerationJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    # Avoid division by zero if total is somehow 0
    progress = int((job.successful + job.failed) / job.total * 100) if job.total else 0

    return JobStatusResponse(
        job_id=job.id,
        status=job.status,
        total=job.total,
        successful=job.successful,
        failed=job.failed,
        progress=progress,
    )


# ---------------------------------------------------------------------------
# GET /jobs/{job_id}/certificates
# ---------------------------------------------------------------------------

@app.get("/jobs/{job_id}/certificates", response_model=JobCertificatesResponse)
def get_job_certificates(job_id: int, db: Session = Depends(get_db)):
    """Return the result of every individual certificate in a job."""
    job = db.get(GenerationJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    results = []
    for cert in job.certificates:
        download_url = None
        if cert.status == "success":
            download_url = f"/certificates/{job_id}/{cert.certificate_id}"

        results.append(
            CertificateResult(
                certificate_id=cert.certificate_id,
                recipient_name=cert.recipient_name,
                status=cert.status,
                download_url=download_url,
                error=cert.error_message,
            )
        )

    return JobCertificatesResponse(job_id=job_id, certificates=results)


# ---------------------------------------------------------------------------
# GET /certificates/{job_id}/{certificate_id}
# ---------------------------------------------------------------------------

@app.get("/certificates/{job_id}/{certificate_id}")
def download_certificate(job_id: int, certificate_id: str, db: Session = Depends(get_db)):
    """Download the generated PDF for a specific certificate."""
    cert = (
        db.query(Certificate)
        .filter(
            Certificate.job_id == job_id,
            Certificate.certificate_id == certificate_id,
        )
        .first()
    )

    if cert is None:
        raise HTTPException(status_code=404, detail="Certificate not found")

    if cert.status != "success" or not cert.file_path:
        raise HTTPException(
            status_code=404,
            detail="Certificate has not been generated successfully yet",
        )

    if not os.path.exists(cert.file_path):
        raise HTTPException(status_code=404, detail="Certificate file not found on disk")

    return FileResponse(
        path=cert.file_path,
        media_type="application/pdf",
        filename=f"{certificate_id}.pdf",
    )
