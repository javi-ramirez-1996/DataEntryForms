from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class FieldType(str, enum.Enum):
    text = "text"
    number = "number"
    choice = "choice"


class ResponseStatus(str, enum.Enum):
    draft = "draft"
    submitted = "submitted"
    completed = "completed"


class Form(Base):
    __tablename__ = "forms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    fields: Mapped[list[FormField]] = relationship("FormField", back_populates="form", cascade="all, delete-orphan")
    responses: Mapped[list[FormResponse]] = relationship("FormResponse", back_populates="form", cascade="all, delete-orphan")


class FormField(Base):
    __tablename__ = "form_fields"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    form_id: Mapped[int] = mapped_column(ForeignKey("forms.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    field_type: Mapped[FieldType] = mapped_column(Enum(FieldType), nullable=False)
    metadata: Mapped[str | None] = mapped_column(Text, nullable=True)

    form: Mapped[Form] = relationship("Form", back_populates="fields")
    values: Mapped[list[ResponseFieldValue]] = relationship("ResponseFieldValue", back_populates="field", cascade="all, delete-orphan")


class FormResponse(Base):
    __tablename__ = "form_responses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    form_id: Mapped[int] = mapped_column(ForeignKey("forms.id", ondelete="CASCADE"), nullable=False, index=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[ResponseStatus] = mapped_column(Enum(ResponseStatus), default=ResponseStatus.draft)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)

    form: Mapped[Form] = relationship("Form", back_populates="responses")
    values: Mapped[list[ResponseFieldValue]] = relationship("ResponseFieldValue", back_populates="response", cascade="all, delete-orphan")


class ResponseFieldValue(Base):
    __tablename__ = "response_field_values"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    response_id: Mapped[int] = mapped_column(ForeignKey("form_responses.id", ondelete="CASCADE"), nullable=False, index=True)
    field_id: Mapped[int] = mapped_column(ForeignKey("form_fields.id", ondelete="CASCADE"), nullable=False, index=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)

    response: Mapped[FormResponse] = relationship("FormResponse", back_populates="values")
    field: Mapped[FormField] = relationship("FormField", back_populates="values")
