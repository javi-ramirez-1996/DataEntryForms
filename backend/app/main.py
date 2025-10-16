from __future__ import annotations

from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Response
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .reporting import get_form_report
from .schemas import FieldStatisticSchema, FormReportSchema, FormSummarySchema
from .scheduler import configure_report_scheduler
from .security import role_dependency
from .exports import build_csv_report, build_pdf_report

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Data Entry Forms Reporting")
report_scheduler = configure_report_scheduler()


@app.get("/reports/forms/{form_id}", response_model=FormReportSchema)
def read_form_report(
    form_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[str, Depends(role_dependency)],
) -> FormReportSchema:
    try:
        report = get_form_report(db, form_id)
    except ValueError as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=404, detail=str(exc))
    if report_scheduler:
        report_scheduler.schedule_for_form(form_id)
    return FormReportSchema(
        form_id=report.form_id,
        form_name=report.form_name,
        summary=FormSummarySchema(
            total_responses=report.summary.total_responses,
            completed_responses=report.summary.completed_responses,
            completion_rate=report.summary.completion_rate,
        ),
        fields=[
            FieldStatisticSchema(
                id=field.field_id,
                name=field.name,
                type=field.field_type,
                answered_count=field.answered_count,
                response_rate=field.response_rate,
                statistics=field.statistics,
            )
            for field in report.fields
        ],
    )


@app.get("/reports/forms/{form_id}/export")
def export_form_report(
    form_id: int,
    format: str,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[str, Depends(role_dependency)],
):
    try:
        report = get_form_report(db, form_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    if format == "csv":
        csv_buffer = build_csv_report(report)
        headers = {"Content-Disposition": f"attachment; filename=form-{form_id}-report.csv"}
        return Response(content=csv_buffer.getvalue(), media_type="text/csv", headers=headers)
    if format == "pdf":
        pdf_buffer = build_pdf_report(report)
        headers = {"Content-Disposition": f"attachment; filename=form-{form_id}-report.pdf"}
        return Response(content=pdf_buffer.getvalue(), media_type="application/pdf", headers=headers)

    raise HTTPException(status_code=400, detail="Unsupported format requested")
