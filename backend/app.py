"""FastAPI application exposing endpoints for managing PDF form templates."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from backend.database import Base, engine, session_scope
from backend.models.forms import FormTemplate
from backend.pdf_ingest import PDFIngestionError, ingest_pdf

app = FastAPI(title="Data Entry Forms API", version="0.1.0")

# Ensure database tables exist on startup.
Base.metadata.create_all(bind=engine)


def get_session() -> Session:
    with session_scope() as session:
        yield session


@app.post("/forms/upload", response_model=Dict[str, Any], status_code=201)
async def upload_form(
    file: UploadFile = File(...),
    title: str | None = None,
    session: Session = Depends(get_session),
) -> Dict[str, Any]:
    """Receive a PDF upload, parse its fields and persist the template."""

    if file.content_type not in {"application/pdf", "application/x-pdf", "binary/octet-stream"}:
        raise HTTPException(status_code=400, detail="Uploaded file must be a PDF")

    try:
        metadata = ingest_pdf(file, title=title)
    except PDFIngestionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    template = FormTemplate(**metadata)
    session.add(template)
    session.flush()  # Ensure ID is populated before returning.

    return template.as_dict()


@app.get("/forms/{form_id}", response_model=Dict[str, Any])
def get_form(form_id: int, session: Session = Depends(get_session)) -> Dict[str, Any]:
    """Return the stored metadata for a form template."""

    template = session.get(FormTemplate, form_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Form template not found")

    return template.as_dict()
