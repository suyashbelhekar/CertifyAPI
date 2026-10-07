"""
Pydantic schemas for request validation and response serialization.
FastAPI uses these for automatic 422 validation errors on bad input.
"""

from datetime import date
from typing import List, Optional
from pydantic import BaseModel, EmailStr, field_validator, model_validator


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class RecipientIn(BaseModel):
    name: str
    email: EmailStr
    certificate_id: str

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("name cannot be blank")
        return v.strip()

    @field_validator("certificate_id")
    @classmethod
    def cert_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("certificate_id cannot be blank")
        return v.strip()


class JobCreateRequest(BaseModel):
    event_name: str
    event_date: date
    recipients: List[RecipientIn]

    @field_validator("event_name")
    @classmethod
    def event_name_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("event_name cannot be blank")
        return v.strip()

    @field_validator("recipients")
    @classmethod
    def recipients_must_not_be_empty(cls, v: List[RecipientIn]) -> List[RecipientIn]:
        if len(v) == 0:
            raise ValueError("recipients list must contain at least one recipient")
        return v

    @model_validator(mode="after")
    def certificate_ids_must_be_unique(self) -> "JobCreateRequest":
        ids = [r.certificate_id for r in self.recipients]
        if len(ids) != len(set(ids)):
            raise ValueError("certificate_id values must be unique within the request")
        return self


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class JobCreateResponse(BaseModel):
    job_id: int
    status: str
    total: int


class JobStatusResponse(BaseModel):
    job_id: int
    status: str
    total: int
    successful: int
    failed: int
    progress: int  # 0-100 percentage


class CertificateResult(BaseModel):
    certificate_id: str
    recipient_name: str
    status: str
    download_url: Optional[str] = None
    error: Optional[str] = None


class JobCertificatesResponse(BaseModel):
    job_id: int
    certificates: List[CertificateResult]
