"""Utilities for ingesting PDF form templates."""

from __future__ import annotations

import io
from typing import Any, Dict, List, Optional

from fastapi import UploadFile
from PyPDF2 import PdfReader


class PDFIngestionError(RuntimeError):
    """Raised when a PDF cannot be parsed."""


def _normalise_field(field: Dict[str, Any]) -> Dict[str, Any]:
    """Normalise a raw PDF field into the structure expected by the frontend."""

    return {
        "name": field.get("/T") or field.get("name"),
        "type": field.get("/FT") or field.get("type"),
        "value": field.get("/V"),
        "options": field.get("/Opt"),
    }


def extract_form_fields(file_bytes: bytes) -> List[Dict[str, Any]]:
    """Extract form field metadata from a PDF document."""

    try:
        pdf = PdfReader(io.BytesIO(file_bytes))
    except Exception as exc:  # pragma: no cover - safety net for unexpected PDF errors.
        raise PDFIngestionError("Unable to read PDF") from exc

    fields: List[Dict[str, Any]] = []

    if pdf.trailer is None:
        return fields

    form = pdf.trailer.get("/Root", {}).get("/AcroForm") if hasattr(pdf, "trailer") else None

    if form and form.get("/Fields"):
        for field in form.get("/Fields", []):
            resolved = field.get_object()
            fields.append(_normalise_field(resolved))

    # Fallback: attempt to use get_fields helper if available.
    try:
        from PyPDF2._utils import deprecation_with_replacement  # type: ignore
    except Exception:  # pragma: no cover
        deprecation_with_replacement = None

    if hasattr(pdf, "get_fields"):
        pdf_fields = pdf.get_fields() or {}
        for key, value in pdf_fields.items():
            normalised = _normalise_field({"/T": key, **value})
            if normalised not in fields:
                fields.append(normalised)

    return fields


def ingest_pdf(upload: UploadFile, *, title: Optional[str] = None) -> Dict[str, Any]:
    """Read an uploaded PDF and produce metadata ready for persistence."""

    file_bytes = upload.file.read()
    if not file_bytes:
        raise PDFIngestionError("Uploaded file is empty")

    fields = extract_form_fields(file_bytes)

    return {
        "filename": upload.filename,
        "title": title or upload.filename,
        "fields": fields,
    }
