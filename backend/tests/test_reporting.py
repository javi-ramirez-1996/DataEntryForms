from __future__ import annotations

from backend.app.reporting import get_form_report


def test_form_report_aggregation(db_session, seeded_data):
    form = seeded_data["form"]
    report = get_form_report(db_session, form.id)

    assert report.summary.total_responses == 3
    assert report.summary.completed_responses == 2
    assert report.summary.completion_rate == 2 / 3

    number_field = next(field for field in report.fields if field.name == "Hazards Found")
    assert number_field.statistics["count"] == 2
    assert number_field.statistics["average"] == 6.0
    assert number_field.statistics["min"] == 5.0
    assert number_field.statistics["max"] == 7.0

    choice_field = next(field for field in report.fields if field.name == "Site Status")
    assert choice_field.statistics == {"distribution": {"Open": 1, "Closed": 1}}

    text_field = next(field for field in report.fields if field.name == "Notes")
    assert text_field.statistics["count"] == 1


def test_report_requires_existing_form(db_session):
    try:
        get_form_report(db_session, 999)
    except ValueError as exc:
        assert "not found" in str(exc)
    else:  # pragma: no cover - defensive
        raise AssertionError("Expected ValueError for missing form")
