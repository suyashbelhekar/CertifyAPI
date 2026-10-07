"""
Tests for Pydantic input validation — all bad inputs should return HTTP 422.
"""


def _post(client, payload):
    return client.post("/jobs", json=payload)


# ---- email -----------------------------------------------------------------

def test_invalid_email_returns_422(client):
    payload = {
        "event_name": "Workshop",
        "event_date": "2026-10-07",
        "recipients": [
            {"name": "Alice", "email": "not-an-email", "certificate_id": "C-001"},
        ],
    }
    assert _post(client, payload).status_code == 422


# ---- name ------------------------------------------------------------------

def test_missing_name_returns_422(client):
    payload = {
        "event_name": "Workshop",
        "event_date": "2026-10-07",
        "recipients": [
            {"email": "alice@example.com", "certificate_id": "C-001"},
        ],
    }
    assert _post(client, payload).status_code == 422


def test_blank_name_returns_422(client):
    payload = {
        "event_name": "Workshop",
        "event_date": "2026-10-07",
        "recipients": [
            {"name": "   ", "email": "alice@example.com", "certificate_id": "C-001"},
        ],
    }
    assert _post(client, payload).status_code == 422


# ---- recipients list -------------------------------------------------------

def test_empty_recipients_returns_422(client):
    payload = {
        "event_name": "Workshop",
        "event_date": "2026-10-07",
        "recipients": [],
    }
    assert _post(client, payload).status_code == 422


def test_missing_recipients_returns_422(client):
    payload = {"event_name": "Workshop", "event_date": "2026-10-07"}
    assert _post(client, payload).status_code == 422


# ---- event fields ----------------------------------------------------------

def test_missing_event_name_returns_422(client):
    payload = {
        "event_date": "2026-10-07",
        "recipients": [
            {"name": "Alice", "email": "alice@example.com", "certificate_id": "C-001"},
        ],
    }
    assert _post(client, payload).status_code == 422


def test_blank_event_name_returns_422(client):
    payload = {
        "event_name": "",
        "event_date": "2026-10-07",
        "recipients": [
            {"name": "Alice", "email": "alice@example.com", "certificate_id": "C-001"},
        ],
    }
    assert _post(client, payload).status_code == 422


def test_missing_event_date_returns_422(client):
    payload = {
        "event_name": "Workshop",
        "recipients": [
            {"name": "Alice", "email": "alice@example.com", "certificate_id": "C-001"},
        ],
    }
    assert _post(client, payload).status_code == 422


# ---- duplicate certificate IDs ---------------------------------------------

def test_duplicate_certificate_ids_returns_422(client):
    payload = {
        "event_name": "Workshop",
        "event_date": "2026-10-07",
        "recipients": [
            {"name": "Alice", "email": "alice@example.com", "certificate_id": "CERT-DUP"},
            {"name": "Bob",   "email": "bob@example.com",   "certificate_id": "CERT-DUP"},
        ],
    }
    assert _post(client, payload).status_code == 422


def test_duplicate_certificate_ids_error_message(client):
    """The 422 body should mention the duplication problem."""
    payload = {
        "event_name": "Workshop",
        "event_date": "2026-10-07",
        "recipients": [
            {"name": "Alice", "email": "alice@example.com", "certificate_id": "SAME"},
            {"name": "Bob",   "email": "bob@example.com",   "certificate_id": "SAME"},
        ],
    }
    body = _post(client, payload).json()
    detail_str = str(body).lower()
    assert "unique" in detail_str or "duplicate" in detail_str or "cert" in detail_str
