from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from .models import FieldType


class FieldStatisticSchema(BaseModel):
    id: int
    name: str
    type: FieldType
    answered_count: int
    response_rate: float
    statistics: dict[str, Any]

    model_config = ConfigDict(json_encoders={FieldType: lambda v: v.value})


class FormSummarySchema(BaseModel):
    total_responses: int
    completed_responses: int
    completion_rate: float


class FormReportSchema(BaseModel):
    form_id: int
    form_name: str
    summary: FormSummarySchema
    fields: list[FieldStatisticSchema]
