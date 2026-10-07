"""
Tests for GET /certificates/{job_id}/{certificate_id} — the download endpoint.
"""


def _create_and_complete_job(client, recipients):
    """Helper: POST /jobs, wait for background task, return job data."""
    payload = {
        "event_name": "Download Test Event",
        "event_date": "2026-10-07",
        "recipients": recipients,
    }
    resp = client.post("/jobs", json=payload)
    assert resp.status_code == 202
    return resp.json()


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

def test_download_successful_certificate_returns_200(client):
    """A successfully generated certificate must be downloadable."""
    job = _create_and_complete_job(client, [
        {"name": "Alice", "email": "alice@example.com", "certificate_id": "CERT-DL-001"},
    ])

    resp = client.get(f"/certificates/{job['job_id']}/CERT-DL-001")
    assert resp.status_code == 200


def test_download_returns_pdf_content_type(client):
    """Downloaded file must have application/pdf content type."""
    job = _create_and_complete_job(client, [
        {"name": "Alice", "email": "alice@example.com", "certificate_id": "CERT-DL-002"},
    ])

    resp = client.get(f"/certificates/{job['job_id']}/CERT-DL-002")
    assert resp.status_code == 200
    assert "application/pdf" in resp.headers.get("content-type", "")


def test_download_response_has_content(client):
    """The downloaded PDF must not be empty."""
    job = _create_and_complete_job(client, [
        {"name": "Bob", "email": "bob@example.com", "certificate_id": "CERT-DL-003"},
    ])

    resp = client.get(f"/certificates/{job['job_id']}/CERT-DL-003")
    assert resp.status_code == 200
    assert len(resp.content) > 0


def test_download_pdf_starts_with_pdf_magic_bytes(client):
    """ReportLab PDFs start with the bytes '%PDF'."""
    job = _create_and_complete_job(client, [
        {"name": "Carol", "email": "carol@example.com", "certificate_id": "CERT-DL-004"},
    ])

    resp = client.get(f"/certificates/{job['job_id']}/CERT-DL-004")
    assert resp.status_code == 200
    assert resp.content[:4] == b"%PDF"


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------

def test_download_nonexistent_job_returns_404(client):
    """Requesting a certificate for a non-existent job must return 404."""
    resp = client.get("/certificates/99999/CERT-XYZ")
    assert resp.status_code == 404


def test_download_nonexistent_cert_id_returns_404(client):
    """Requesting a certificate_id that was never created must return 404."""
    job = _create_and_complete_job(client, [
        {"name": "Alice", "email": "alice@example.com", "certificate_id": "CERT-REAL"},
    ])

    resp = client.get(f"/certificates/{job['job_id']}/CERT-DOES-NOT-EXIST")
    assert resp.status_code == 404


def test_download_failed_certificate_returns_404(client):
    """A certificate that failed generation must not be downloadable."""
    job = _create_and_complete_job(client, [
        {"name": "FAIL_TEST", "email": "fail@example.com", "certificate_id": "CERT-FAIL"},
    ])

    resp = client.get(f"/certificates/{job['job_id']}/CERT-FAIL")
    assert resp.status_code == 404
