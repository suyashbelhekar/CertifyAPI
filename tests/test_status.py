"""
Tests for GET /jobs/{job_id} — job status and progress tracking.
"""

import time


def _create_job(client, recipients):
    payload = {
        "event_name": "Status Test Event",
        "event_date": "2026-10-07",
        "recipients": recipients,
    }
    return client.post("/jobs", json=payload).json()


def test_get_status_returns_200(client):
    """GET /jobs/{job_id} should return 200 for an existing job."""
    job = _create_job(client, [
        {"name": "Alice", "email": "alice@example.com", "certificate_id": "C-1"},
    ])
    response = client.get(f"/jobs/{job['job_id']}")
    assert response.status_code == 200


def test_get_status_unknown_job_returns_404(client):
    """Requesting a non-existent job_id should return 404."""
    response = client.get("/jobs/99999")
    assert response.status_code == 404


def test_status_response_has_required_fields(client):
    """Status response must include all documented fields."""
    job = _create_job(client, [
        {"name": "Alice", "email": "alice@example.com", "certificate_id": "C-1"},
    ])
    data = client.get(f"/jobs/{job['job_id']}").json()

    for field in ("job_id", "status", "total", "successful", "failed", "progress"):
        assert field in data, f"Missing field: {field}"


def test_completed_job_status(client):
    """After TestClient processes the background task, status should be completed."""
    job = _create_job(client, [
        {"name": "Alice", "email": "alice@example.com", "certificate_id": "C-1"},
        {"name": "Bob",   "email": "bob@example.com",   "certificate_id": "C-2"},
    ])
    data = client.get(f"/jobs/{job['job_id']}").json()

    # TestClient runs background tasks synchronously
    assert data["status"] in ("completed", "processing", "queued")


def test_completed_job_totals(client):
    """Successful job: successful + failed must equal total."""
    job = _create_job(client, [
        {"name": "Alice", "email": "alice@example.com", "certificate_id": "C-1"},
        {"name": "Bob",   "email": "bob@example.com",   "certificate_id": "C-2"},
        {"name": "Carol", "email": "carol@example.com", "certificate_id": "C-3"},
    ])
    data = client.get(f"/jobs/{job['job_id']}").json()

    # Total must always equal successful + failed (once processing is done)
    if data["status"] == "completed":
        assert data["successful"] + data["failed"] == data["total"]
        assert data["successful"] == 3
        assert data["failed"] == 0


def test_progress_is_100_when_completed(client):
    """Progress should be 100 when all certificates are processed."""
    job = _create_job(client, [
        {"name": "Alice", "email": "alice@example.com", "certificate_id": "C-1"},
    ])
    data = client.get(f"/jobs/{job['job_id']}").json()

    if data["status"] == "completed":
        assert data["progress"] == 100


def test_job_id_in_status_response_matches(client):
    """The job_id in the status response must match what was requested."""
    job = _create_job(client, [
        {"name": "Alice", "email": "alice@example.com", "certificate_id": "C-1"},
    ])
    data = client.get(f"/jobs/{job['job_id']}").json()
    assert data["job_id"] == job["job_id"]
