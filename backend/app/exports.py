from __future__ import annotations

import io

from fpdf import FPDF

from .reporting import FormReport


def build_csv_report(report: FormReport) -> io.StringIO:
    buffer = io.StringIO()
    buffer.write("Form ID,Form Name\n")
    buffer.write(f"{report.form_id},{report.form_name}\n\n")
    buffer.write("Metric,Value\n")
    buffer.write(f"Total Responses,{report.summary.total_responses}\n")
    buffer.write(f"Completed Responses,{report.summary.completed_responses}\n")
    buffer.write(f"Completion Rate,{report.summary.completion_rate:.2%}\n\n")

    buffer.write("Field,Type,Answered Count,Response Rate,Details\n")
    for field in report.fields:
        detail_summary = _format_field_detail(field.statistics)
        buffer.write(
            f"{field.name},{field.field_type.value},{field.answered_count},{field.response_rate:.2%},{detail_summary}\n"
        )
    buffer.seek(0)
    return buffer


def _format_field_detail(statistics: dict[str, object]) -> str:
    parts: list[str] = []
    for key, value in statistics.items():
        parts.append(f"{key}={value}")
    return " | ".join(parts)


def build_pdf_report(report: FormReport) -> io.BytesIO:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Form Report: {report.form_name}", ln=True, align="C")
    pdf.ln(5)

    pdf.set_font("Arial", size=10)
    pdf.cell(0, 8, txt=f"Total Responses: {report.summary.total_responses}", ln=True)
    pdf.cell(0, 8, txt=f"Completed Responses: {report.summary.completed_responses}", ln=True)
    pdf.cell(0, 8, txt=f"Completion Rate: {report.summary.completion_rate:.2%}", ln=True)
    pdf.ln(4)

    for field in report.fields:
        pdf.set_font("Arial", style="B", size=10)
        pdf.cell(0, 8, txt=f"{field.name} ({field.field_type.value})", ln=True)
        pdf.set_font("Arial", size=10)
        pdf.cell(0, 6, txt=f"Answered: {field.answered_count}", ln=True)
        pdf.cell(0, 6, txt=f"Response Rate: {field.response_rate:.2%}", ln=True)
        for key, value in field.statistics.items():
            pdf.cell(0, 6, txt=f"{key.title()}: {value}", ln=True)
        pdf.ln(2)

    buffer = io.BytesIO(pdf.output(dest="S").encode("latin1"))
    buffer.seek(0)
    return buffer
