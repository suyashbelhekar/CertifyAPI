"""
Tests for the certificate.py generation module directly —
no HTTP layer involved.
"""

import os
import tempfile
from datetime import date

import pytest

from app.certificate import generate_certificate


def test_generate_certificate_creates_pdf(tmp_path):
    """A PDF file must exist at the returned path after generation."""
    output_path = str(tmp_path / "test_cert.pdf")

    result = generate_certificate(
        recipient_name="Suyash Belhekar",
        recipient_email="suyash@example.com",
        certificate_id="CERT-001",
        event_name="Python Workshop",
        event_date=date(2026, 10, 7),
        output_path=output_path,
    )

    assert result == output_path
    assert os.path.exists(output_path)


def test_generated_pdf_is_not_empty(tmp_path):
    """The PDF should have a non-zero file size."""
    output_path = str(tmp_path / "test_cert.pdf")

    generate_certificate(
        recipient_name="Rahul Patil",
        recipient_email="rahul@example.com",
        certificate_id="CERT-002",
        event_name="Python Workshop",
        event_date=date(2026, 10, 7),
        output_path=output_path,
    )

    assert os.path.getsize(output_path) > 0


def test_generate_certificate_with_string_date(tmp_path):
    """event_date can be passed as a string and should not raise."""
    output_path = str(tmp_path / "test_cert_str_date.pdf")

    generate_certificate(
        recipient_name="Test User",
        recipient_email="test@example.com",
        certificate_id="CERT-STR",
        event_name="Test Event",
        event_date="2026-10-07",
        output_path=output_path,
    )

    assert os.path.exists(output_path)


def test_generate_certificate_creates_parent_directories(tmp_path):
    """The function must create any missing parent directories."""
    nested_path = str(tmp_path / "subdir" / "deep" / "cert.pdf")

    generate_certificate(
        recipient_name="Deep User",
        recipient_email="deep@example.com",
        certificate_id="CERT-DEEP",
        event_name="Nested Test",
        event_date=date(2026, 1, 1),
        output_path=nested_path,
    )

    assert os.path.exists(nested_path)


def test_fail_test_name_raises_exception(tmp_path):
    """FAIL_TEST recipient name must raise an exception (used in failure tests)."""
    output_path = str(tmp_path / "should_not_exist.pdf")

    with pytest.raises(ValueError, match="FAIL_TEST"):
        generate_certificate(
            recipient_name="FAIL_TEST",
            recipient_email="fail@example.com",
            certificate_id="CERT-FAIL",
            event_name="Test Event",
            event_date=date(2026, 10, 7),
            output_path=output_path,
        )

    # File must NOT have been created
    assert not os.path.exists(output_path)
