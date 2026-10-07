# Bulk Certificate Generator — Backend API

A clean, interview-ready REST API that generates PDF certificates in bulk.
One POST request submits multiple recipients; the API creates a job, validates
all input, generates individual PDFs in the background, tracks progress, and
lets clients poll for status and download each certificate.

---

## Features

- Submit multiple recipients in one request
- Input validation with clear 422 error messages
- Background PDF generation (non-blocking response)
- Per-certificate failure isolation — one bad record never stops the rest
- Job progress tracking (queued → processing → completed / completed_with_errors / failed)
- PDF download endpoint
- SQLite persistence via SQLAlchemy ORM
- Fully tested with pytest + FastAPI TestClient

---

## Technology Stack

| Layer         | Library              |
|---------------|----------------------|
| Web framework | FastAPI              |
| Database      | SQLite + SQLAlchemy  |
| Validation    | Pydantic v2          |
| PDF engine    | ReportLab            |
| Testing       | pytest + httpx       |
| Server        | Uvicorn              |

---

## Project Structure

```
bulk-certificate-generator/
├── app/
│   ├── __init__.py        # package marker
│   ├── main.py            # FastAPI app + all endpoints
│   ├── database.py        # SQLAlchemy engine & session factory
│   ├── models.py          # ORM models (GenerationJob, Certificate)
│   ├── schemas.py         # Pydantic request/response schemas
│   ├── certificate.py     # ReportLab PDF generation
│   └── services.py        # bulk processing business logic
├── generated/             # output PDFs (git-ignored)
├── tests/
│   ├── conftest.py        # shared fixtures (test DB, temp dir, TestClient)
│   ├── test_jobs.py       # POST /jobs tests
│   ├── test_validation.py # input validation tests
│   ├── test_certificate.py# PDF generation unit tests
│   ├── test_status.py     # GET /jobs/{id} tests
│   ├── test_failure.py    # failure isolation tests
│   └── test_download.py   # certificate download tests
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Installation

```bash
# 1. Clone / enter project
cd bulk-certificate-generator

# 2. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt
```

---

## Run the Application

```bash
uvicorn app.main:app --reload
```

Open interactive docs: **http://127.0.0.1:8000/docs**

---

## Run Tests

```bash
pytest
```

For verbose output:

```bash
pytest -v
```

---

## API Endpoints

| Method | Path                                   | Description                        |
|--------|----------------------------------------|------------------------------------|
| POST   | `/jobs`                                | Create a bulk generation job       |
| GET    | `/jobs/{job_id}`                       | Get job status and progress        |
| GET    | `/jobs/{job_id}/certificates`          | List all certificate results       |
| GET    | `/certificates/{job_id}/{cert_id}`     | Download a generated PDF           |

---

## Example Requests & Responses

### POST /jobs

**Request:**
```json
{
  "event_name": "Python Workshop",
  "event_date": "2026-10-07",
  "recipients": [
    {
      "name": "Suyash Belhekar",
      "email": "suyash@example.com",
      "certificate_id": "CERT-001"
    },
    {
      "name": "Rahul Patil",
      "email": "rahul@example.com",
      "certificate_id": "CERT-002"
    }
  ]
}
```

**Response — HTTP 202:**
```json
{
  "job_id": 1,
  "status": "queued",
  "total": 2
}
```

---

### GET /jobs/1

**Response — HTTP 200:**
```json
{
  "job_id": 1,
  "status": "completed",
  "total": 2,
  "successful": 2,
  "failed": 0,
  "progress": 100
}
```

**Possible status values:**

| Status                  | Meaning                                  |
|-------------------------|------------------------------------------|
| `queued`                | Job created, not yet started             |
| `processing`            | PDFs are being generated                 |
| `completed`             | All certificates generated successfully  |
| `completed_with_errors` | Some succeeded, some failed              |
| `failed`                | Every certificate failed                 |

---

### GET /jobs/1/certificates

**Response — HTTP 200:**
```json
{
  "job_id": 1,
  "certificates": [
    {
      "certificate_id": "CERT-001",
      "recipient_name": "Suyash Belhekar",
      "status": "success",
      "download_url": "/certificates/1/CERT-001",
      "error": null
    },
    {
      "certificate_id": "CERT-002",
      "recipient_name": "Rahul Patil",
      "status": "failed",
      "download_url": null,
      "error": "Intentional test failure"
    }
  ]
}
```

---

### GET /certificates/1/CERT-001

Returns the PDF file directly (`application/pdf`).
Use this URL in a browser or with curl:

```bash
curl -O http://127.0.0.1:8000/certificates/1/CERT-001
```

---

## Design Decisions

### Why BackgroundTasks instead of Celery/Redis?

FastAPI's built-in `BackgroundTasks` was chosen because:

1. **Simplicity** — no external broker or worker processes to run.
2. **Responsive API** — the HTTP response is returned immediately; processing
   happens after the response is sent.
3. **Demonstrates async processing** — the client must poll, which is the
   correct pattern for long-running operations.
4. **Interview clarity** — the entire system can be explained and run from a
   single `uvicorn` command.

For a production workload (thousands of recipients, retries, distributed
workers) a proper task queue such as **Celery + Redis** or **RQ** would be
more appropriate.

---

### Why SQLite?

Zero-configuration file-based database that requires no separate server.
SQLAlchemy abstracts the dialect, so swapping to PostgreSQL requires only
changing the `DATABASE_URL` string in `database.py`.

---

### Failure Isolation

Each certificate is generated inside its own `try/except` block in
`services.py`. A failure in one recipient sets that certificate's status to
`failed` and records the error message, then processing continues with the
next recipient. The final job status reflects the outcome:

```
all ok        → completed
some failed   → completed_with_errors
all failed    → failed
```

Internal stack traces are never exposed through the API — only the exception
message is stored.

---

## Limitations & Production Improvements

| Current (demo)               | Production improvement                     |
|------------------------------|--------------------------------------------|
| BackgroundTasks              | Celery + Redis / RQ for reliability        |
| SQLite                       | PostgreSQL for concurrency                 |
| Local filesystem storage     | S3 / object storage for generated PDFs    |
| No authentication            | JWT / API key middleware                   |
| Single uvicorn process       | Gunicorn with multiple workers             |
| No retry logic               | Retry failed certificates automatically   |
| No pagination on list endpoints | Cursor-based pagination               |
