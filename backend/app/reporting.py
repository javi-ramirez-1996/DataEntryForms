from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from sqlalchemy import Float, cast, func, select
from sqlalchemy.orm import Session

from .models import FieldType, Form, FormField, FormResponse, ResponseFieldValue, ResponseStatus


@dataclass
class FieldStatistic:
    field_id: int
    name: str
    field_type: FieldType
    answered_count: int
    response_rate: float
    statistics: dict[str, Any]


@dataclass
class FormSummary:
    total_responses: int
    completed_responses: int
    completion_rate: float


@dataclass
class FormReport:
    form_id: int
    form_name: str
    summary: FormSummary
    fields: list[FieldStatistic]


def _calculate_numeric_stats(session: Session, field: FormField, completed_response_ids: list[int]) -> dict[str, Any]:
    numeric_values_stmt = (
        select(
            func.count(ResponseFieldValue.id),
            func.avg(cast(ResponseFieldValue.value, Float)),
            func.min(cast(ResponseFieldValue.value, Float)),
            func.max(cast(ResponseFieldValue.value, Float)),
        )
        .where(ResponseFieldValue.field_id == field.id)
        .where(ResponseFieldValue.response_id.in_(completed_response_ids))
    )
    count, avg, min_value, max_value = session.execute(numeric_values_stmt).one()
    return {
        "count": int(count or 0),
        "average": float(avg) if avg is not None else None,
        "min": float(min_value) if min_value is not None else None,
        "max": float(max_value) if max_value is not None else None,
    }


def _calculate_choice_stats(session: Session, field: FormField, completed_response_ids: list[int]) -> dict[str, Any]:
    choice_stmt = (
        select(ResponseFieldValue.value, func.count(ResponseFieldValue.id))
        .where(ResponseFieldValue.field_id == field.id)
        .where(ResponseFieldValue.response_id.in_(completed_response_ids))
        .group_by(ResponseFieldValue.value)
    )
    distribution = {
        choice: int(count)
        for choice, count in session.execute(choice_stmt).all()
    }
    return {"distribution": distribution}


def _calculate_text_stats(session: Session, field: FormField, completed_response_ids: list[int]) -> dict[str, Any]:
    text_stmt = (
        select(func.count(ResponseFieldValue.id))
        .where(ResponseFieldValue.field_id == field.id)
        .where(ResponseFieldValue.response_id.in_(completed_response_ids))
    )
    answered = session.execute(text_stmt).scalar() or 0
    return {"count": int(answered)}


_FIELD_STAT_CALCULATORS = {
    FieldType.number: _calculate_numeric_stats,
    FieldType.choice: _calculate_choice_stats,
    FieldType.text: _calculate_text_stats,
}


def get_form_report(session: Session, form_id: int) -> FormReport:
    form: Form | None = session.get(Form, form_id)
    if form is None:
        raise ValueError(f"Form {form_id} not found")

    total_responses_stmt = select(func.count(FormResponse.id)).where(FormResponse.form_id == form_id)
    total_responses = session.execute(total_responses_stmt).scalar() or 0

    completed_stmt = (
        select(func.count(FormResponse.id), func.group_concat(FormResponse.id, ","))
        .where(FormResponse.form_id == form_id)
        .where(FormResponse.status == ResponseStatus.completed)
        .where(FormResponse.is_completed.is_(True))
    )
    completed_count, completed_concat = session.execute(completed_stmt).one()
    completed_responses = int(completed_count or 0)
    completed_ids = (
        [int(value) for value in completed_concat.split(",")] if completed_concat else []
    )

    completion_rate = (completed_responses / total_responses) if total_responses else 0.0

    field_statistics: list[FieldStatistic] = []
    answered_counts: dict[int, int] = defaultdict(int)
    if completed_ids:
        answered_stmt = (
            select(ResponseFieldValue.field_id, func.count(ResponseFieldValue.id))
            .where(ResponseFieldValue.response_id.in_(completed_ids))
            .group_by(ResponseFieldValue.field_id)
        )
        for field_id, count in session.execute(answered_stmt).all():
            answered_counts[int(field_id)] = int(count)

    for field in form.fields:
        stats_func = _FIELD_STAT_CALCULATORS[field.field_type]
        statistics = stats_func(session, field, completed_ids)
        answered = answered_counts.get(field.id, 0)
        response_rate = (answered / completed_responses) if completed_responses else 0.0
        field_statistics.append(
            FieldStatistic(
                field_id=field.id,
                name=field.name,
                field_type=field.field_type,
                answered_count=answered,
                response_rate=response_rate,
                statistics=statistics,
            )
        )

    summary = FormSummary(
        total_responses=int(total_responses),
        completed_responses=completed_responses,
        completion_rate=completion_rate,
    )

    return FormReport(
        form_id=form.id,
        form_name=form.name,
        summary=summary,
        fields=field_statistics,
    )
