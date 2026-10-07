"""
Tests for POST /jobs — creating a generation job.
"""


def test_create_job_returns_202(client):
    """Submitting a valid job should return HTTP 202."""
    payload = {
        "event_name": "Python Workshop",
        "event_date": "2026-10-07",
        "recipients": [
            {"name": "Alice", "email": "alice@example.com", "certificate_id": "CERT-001"},
            {"name": "Bob",   "email": "bob@example.com",   "certificate_id": "CERT-002"},
        ],
    }
    response = client.post("/jobs", json=payload)
    assert response.status_code == 202


def test_create_job_returns_job_id(client):
    """Response must contain a valid integer job_id."""
    payload = {
        "event_name": "Python Workshop",
        "event_date": "2026-10-07",
        "recipients": [
            {"name": "Alice", "email": "alice@example.com", "certificate_id": "CERT-001"},
        ],
    }
    response = client.post("/jobs", json=payload)
    data = response.json()
    assert "job_id" in data
    assert isinstance(data["job_id"], int)
    assert data["job_id"] >= 1


def test_create_job_returns_correct_total(client):
    """The 'total' field must equal the number of recipients submitted."""
    recipients = [
        {"name": f"Person {i}", "email": f"person{i}@example.com", "certificate_id": f"C-{i:03d}"}
        for i in range(1, 6)
    ]
    payload = {"event_name": "Workshop", "event_date": "2026-10-07", "recipients": recipients}
    data = client.post("/jobs", json=payload).json()
    assert data["total"] == 5


def test_create_job_initial_status_queued_or_completed(client):
    """
    Status starts as 'queued'.  With TestClient, BackgroundTasks run
    synchronously so by the time we read the response it may already
    be 'completed' — both are acceptable here.
    """
    payload = {
        "event_name": "Workshop",
        "event_date": "2026-10-07",
        "recipients": [
            {"name": "Alice", "email": "alice@example.com", "certificate_id": "C-001"},
        ],
    }
    data = client.post("/jobs", json=payload).json()
    assert data["status"] in ("queued", "completed", "processing")


def test_multiple_jobs_get_unique_ids(client):
    """Each submitted job should receive a different job_id."""
    base_payload = {
        "event_name": "Event",
        "event_date": "2026-10-07",
        "recipients": [{"name": "A", "email": "a@x.com", "certificate_id": "C-1"}],
    }
    id1 = client.post("/jobs", json=base_payload).json()["job_id"]

    base_payload["recipients"][0]["certificate_id"] = "C-2"
    id2 = client.post("/jobs", json=base_payload).json()["job_id"]

    assert id1 != id2
