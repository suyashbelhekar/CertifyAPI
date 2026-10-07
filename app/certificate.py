"""
PDF certificate generation using ReportLab.

generate_certificate() creates one PDF file per recipient and returns
the file path. All design is done in code — no external template file needed.
"""

import os
from datetime import date

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.pdfgen import canvas


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_certificate(
    recipient_name: str,
    recipient_email: str,
    certificate_id: str,
    event_name: str,
    event_date: date | str,
    output_path: str,
) -> str:
    """
    Generate a single PDF certificate and save it to output_path.

    Returns the output_path on success.
    Raises an exception if something goes wrong (caller handles it).

    Special case for testing: if recipient_name == "FAIL_TEST" we raise
    an exception intentionally so tests can verify failure isolation.
    """
    if recipient_name == "FAIL_TEST":
        raise ValueError("Intentional test failure for recipient FAIL_TEST")

    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Normalise event_date to a readable string
    if isinstance(event_date, date):
        date_str = event_date.strftime("%B %d, %Y")   # e.g. "October 07, 2026"
    else:
        date_str = str(event_date)

    _draw_certificate(
        output_path=output_path,
        recipient_name=recipient_name,
        event_name=event_name,
        date_str=date_str,
        certificate_id=certificate_id,
    )

    return output_path


# ---------------------------------------------------------------------------
# Private drawing helper
# ---------------------------------------------------------------------------

def _draw_certificate(
    output_path: str,
    recipient_name: str,
    event_name: str,
    date_str: str,
    certificate_id: str,
) -> None:
    """Draw all the visual elements of the certificate onto the canvas."""

    page_width, page_height = landscape(A4)
    c = canvas.Canvas(output_path, pagesize=landscape(A4))

    # ---- Background --------------------------------------------------------
    c.setFillColor(colors.HexColor("#FAFAF8"))
    c.rect(0, 0, page_width, page_height, fill=True, stroke=False)

    # ---- Outer border ------------------------------------------------------
    border_margin = 1.2 * cm
    c.setStrokeColor(colors.HexColor("#1A3C5E"))
    c.setLineWidth(3)
    c.rect(border_margin, border_margin,
           page_width - 2 * border_margin, page_height - 2 * border_margin,
           fill=False, stroke=True)

    # ---- Inner decorative border -------------------------------------------
    inner_margin = 1.7 * cm
    c.setStrokeColor(colors.HexColor("#C9A84C"))
    c.setLineWidth(1.2)
    c.rect(inner_margin, inner_margin,
           page_width - 2 * inner_margin, page_height - 2 * inner_margin,
           fill=False, stroke=True)

    # ---- Organization name (top) -------------------------------------------
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(colors.HexColor("#C9A84C"))
    c.drawCentredString(page_width / 2, page_height - 3.2 * cm, "DEMO ORGANIZATION")

    # ---- Main title --------------------------------------------------------
    c.setFont("Helvetica-Bold", 32)
    c.setFillColor(colors.HexColor("#1A3C5E"))
    c.drawCentredString(page_width / 2, page_height - 5.5 * cm,
                        "CERTIFICATE OF PARTICIPATION")

    # ---- Horizontal rule under title ---------------------------------------
    rule_y = page_height - 6.3 * cm
    c.setStrokeColor(colors.HexColor("#C9A84C"))
    c.setLineWidth(1.5)
    c.line(4 * cm, rule_y, page_width - 4 * cm, rule_y)

    # ---- "This certificate is proudly presented to" ------------------------
    c.setFont("Helvetica", 14)
    c.setFillColor(colors.HexColor("#555555"))
    c.drawCentredString(page_width / 2, page_height - 8.2 * cm,
                        "This certificate is proudly presented to")

    # ---- Recipient name (large) --------------------------------------------
    c.setFont("Helvetica-Bold", 28)
    c.setFillColor(colors.HexColor("#1A3C5E"))
    c.drawCentredString(page_width / 2, page_height - 10.5 * cm, recipient_name)

    # ---- Underline below recipient name ------------------------------------
    name_y = page_height - 11.0 * cm
    c.setStrokeColor(colors.HexColor("#1A3C5E"))
    c.setLineWidth(0.8)
    c.line(6 * cm, name_y, page_width - 6 * cm, name_y)

    # ---- "for participating in" + event name -------------------------------
    c.setFont("Helvetica", 13)
    c.setFillColor(colors.HexColor("#555555"))
    c.drawCentredString(page_width / 2, page_height - 12.5 * cm,
                        "for successfully participating in")

    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(colors.HexColor("#1A3C5E"))
    c.drawCentredString(page_width / 2, page_height - 13.8 * cm, event_name)

    # ---- Date --------------------------------------------------------------
    c.setFont("Helvetica", 12)
    c.setFillColor(colors.HexColor("#555555"))
    c.drawCentredString(page_width / 2, page_height - 15.4 * cm,
                        f"Date: {date_str}")

    # ---- Certificate ID (bottom right) -------------------------------------
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.HexColor("#888888"))
    c.drawRightString(page_width - 2 * cm, 1.8 * cm,
                      f"Certificate ID: {certificate_id}")

    c.save()
