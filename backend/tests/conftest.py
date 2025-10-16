from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.models import FieldType, Form, FormField, FormResponse, ResponseFieldValue, ResponseStatus


@pytest.fixture()
def engine():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session(engine) -> Session:
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def seeded_data(db_session: Session):
    form = Form(name="Site Inspection")
    db_session.add(form)
    db_session.flush()

    number_field = FormField(form_id=form.id, name="Hazards Found", field_type=FieldType.number)
    choice_field = FormField(form_id=form.id, name="Site Status", field_type=FieldType.choice)
    text_field = FormField(form_id=form.id, name="Notes", field_type=FieldType.text)

    db_session.add_all([number_field, choice_field, text_field])
    db_session.flush()

    response_a = FormResponse(
        form_id=form.id,
        status=ResponseStatus.completed,
        is_completed=True,
    )
    response_b = FormResponse(
        form_id=form.id,
        status=ResponseStatus.completed,
        is_completed=True,
    )
    response_c = FormResponse(
        form_id=form.id,
        status=ResponseStatus.submitted,
        is_completed=False,
    )

    db_session.add_all([response_a, response_b, response_c])
    db_session.flush()

    db_session.add_all(
        [
            ResponseFieldValue(response_id=response_a.id, field_id=number_field.id, value="5"),
            ResponseFieldValue(response_id=response_b.id, field_id=number_field.id, value="7"),
            ResponseFieldValue(response_id=response_a.id, field_id=choice_field.id, value="Open"),
            ResponseFieldValue(response_id=response_b.id, field_id=choice_field.id, value="Closed"),
            ResponseFieldValue(response_id=response_b.id, field_id=text_field.id, value="All issues resolved"),
        ]
    )
    db_session.commit()

    return {
        "form": form,
        "fields": {
            "number": number_field,
            "choice": choice_field,
            "text": text_field,
        },
    }


@pytest.fixture()
def client(db_session: Session):
    def _get_db_override():
        try:
            yield db_session
        finally:
            db_session.rollback()

    app.dependency_overrides[get_db] = _get_db_override
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
