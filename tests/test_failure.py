"""
Tests for individual certificate failure isolation.

The special recipient name "FAIL_TEST" triggers an intentional exception
inside certificate.py so we can verify:
  - Other certificates in the same job still succeed.
  - The job ends with status 'completed_with_errors'.
  - Counters (successful / failed) are accurate.
"""


def _create_job(client, recipients):
    payload = {
        "event_name": "Failure Test Event",
        "event_date": "2026-10-07",
        "recipients": recipients,
    }
    resp = client.post("/jobs", json=payload)
    assert resp.status_code == 202
    return resp.json()


def test_single_failure_does_not_stop_others(client):
    """
    Submit 3 recipients: one will fail, two should succeed.
    Verify the job is 'completed_with_errors' and successful == 2.
    """
    job = _create_job(client, [
        {"name": "Alice",     "email": "alice@example.com", "certificate_id": "C-001"},
        {"name": "FAIL_TEST", "email": "fail@example.com",  "certificate_id": "C-002"},
        {"name": "Bob",       "email": "bob@example.com",   "certificate_id": "C-003"},
    ])

    data = client.get(f"/jobs/{job['job_id']}").json()

    assert data["status"] == "completed_with_errors"
    assert data["successful"] == 2
    assert data["failed"] == 1
    assert data["total"] == 3


def test_failed_certificate_has_error_message(client):
    """The failed certificate record must contain an error message."""
    job = _create_job(client, [
        {"name": "Alice",     "email": "alice@example.com", "certificate_id": "C-001"},
        {"name": "FAIL_TEST", "email": "fail@example.com",  "certificate_id": "C-FAIL"},
    ])

    certs = client.get(f"/jobs/{job['job_id']}/certificates").json()["certificates"]

    failed = [c for c in certs if c["certificate_id"] == "C-FAIL"]
    assert len(failed) == 1
    assert failed[0]["status"] == "failed"
    assert failed[0]["error"] is not None
    assert len(failed[0]["error"]) > 0


def test_successful_certificates_have_download_url(client):
    """Certificates that succeeded must have a non-null download_url."""
    job = _create_job(client, [
        {"name": "Alice",     "email": "alice@example.com", "certificate_id": "C-OK"},
        {"name": "FAIL_TEST", "email": "fail@example.com",  "certificate_id": "C-FAIL"},
    ])

    certs = client.get(f"/jobs/{job['job_id']}/certificates").json()["certificates"]

    successful = [c for c in certs if c["status"] == "success"]
    assert len(successful) == 1
    assert successful[0]["download_url"] is not None


def test_all_fail_sets_job_status_failed(client):
    """If every recipient fails the job status must be 'failed'."""
    job = _create_job(client, [
        {"name": "FAIL_TEST", "email": "f1@example.com", "certificate_id": "C-F1"},
        {"name": "FAIL_TEST", "email": "f2@example.com", "certificate_id": "C-F2"},
    ])

    data = client.get(f"/jobs/{job['job_id']}").json()

    assert data["status"] == "failed"
    assert data["successful"] == 0
    assert data["failed"] == 2


def test_progress_reflects_failures(client):
    """progress should still be 100 when all certificates have been attempted."""
    job = _create_job(client, [
        {"name": "Alice",     "email": "alice@example.com", "certificate_id": "C-1"},
        {"name": "FAIL_TEST", "email": "fail@example.com",  "certificate_id": "C-2"},
    ])

    data = client.get(f"/jobs/{job['job_id']}").json()

    if data["status"] in ("completed_with_errors", "failed", "completed"):
        assert data["progress"] == 100
