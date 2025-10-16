"""Data models for storing form metadata extracted from PDFs."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import JSON, Column, DateTime, Integer, String

from backend.database import Base


class FormTemplate(Base):
    """Represents a stored form template extracted from a PDF file."""

    __tablename__ = "form_templates"

    id: int = Column(Integer, primary_key=True, index=True)
    filename: str = Column(String(255), nullable=False)
    title: Optional[str] = Column(String(255), nullable=True)
    fields: List[Dict[str, Any]] = Column(JSON, nullable=False)
    created_at: datetime = Column(DateTime, nullable=False, default=datetime.utcnow)

    def as_dict(self) -> Dict[str, Any]:
        """Return a serialisable representation of the form template."""

        return {
            "id": self.id,
            "filename": self.filename,
            "title": self.title,
            "fields": self.fields,
            "created_at": self.created_at.isoformat(),
        }
