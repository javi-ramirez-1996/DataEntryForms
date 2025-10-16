from __future__ import annotations

from backend.app.exports import build_csv_report, build_pdf_report
from backend.app.reporting import get_form_report


def test_build_csv_report(db_session, seeded_data):
    form = seeded_data["form"]
    report = get_form_report(db_session, form.id)

    csv_buffer = build_csv_report(report)
    csv_content = csv_buffer.getvalue()
    assert "Form ID" in csv_content
    assert "Completion Rate" in csv_content
    assert "Hazards Found" in csv_content
    assert "Site Status" in csv_content


def test_build_pdf_report(db_session, seeded_data):
    form = seeded_data["form"]
    report = get_form_report(db_session, form.id)

    pdf_buffer = build_pdf_report(report)
    pdf_bytes = pdf_buffer.getvalue()
    assert pdf_bytes.startswith(b"%PDF")
    assert b"Form Report" in pdf_bytes
