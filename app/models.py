"""
SQLAlchemy ORM models for the two database tables:
  - GenerationJob  : tracks a bulk job (one per POST /jobs request)
  - Certificate    : tracks each individual recipient within a job
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class GenerationJob(Base):
    __tablename__ = "generation_jobs"

    id = Column(Integer, primary_key=True, index=True)
    event_name = Column(String, nullable=False)
    event_date = Column(String, nullable=False)  # stored as ISO string "YYYY-MM-DD"

    # Possible values: queued | processing | completed | completed_with_errors | failed
    status = Column(String, default="queued", nullable=False)

    total = Column(Integer, default=0)
    successful = Column(Integer, default=0)
    failed = Column(Integer, default=0)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)

    # One job → many certificates
    certificates = relationship("Certificate", back_populates="job")


class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("generation_jobs.id"), nullable=False)

    certificate_id = Column(String, nullable=False)   # user-provided e.g. "CERT-001"
    recipient_name = Column(String, nullable=False)
    recipient_email = Column(String, nullable=False)

    # Possible values: pending | success | failed
    status = Column(String, default="pending", nullable=False)

    file_path = Column(String, nullable=True)     # path to generated PDF
    error_message = Column(String, nullable=True) # set on failure

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    job = relationship("GenerationJob", back_populates="certificates")
