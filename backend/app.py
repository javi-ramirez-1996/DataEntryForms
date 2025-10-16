from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException


@dataclass
class FormField:
    id: str
    label: str
    type: str
    required: bool = False
    options: Optional[List[str]] = None


@dataclass
class FormTemplate:
    id: str
    name: str
    description: str
    fields: List[FormField]


@dataclass
class FormAssignment:
    form_id: str
    user_id: str
    response_id: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "form_id": self.form_id,
            "user_id": self.user_id,
            "response_id": self.response_id,
        }


@dataclass
class FormResponse:
    id: str
    form_id: str
    answers: Dict[str, Optional[str]] = field(default_factory=dict)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    status: str = "Not Started"
    progress: float = 0.0

    def to_dict(self) -> Dict[str, object]:
        payload = asdict(self)
        payload["updated_at"] = self.updated_at.isoformat()
        return payload


app = FastAPI(title="Data Entry Forms API")

FORMS: Dict[str, FormTemplate] = {}
FORM_RESPONSES: Dict[str, FormResponse] = {}
ASSIGNMENTS: Dict[str, FormAssignment] = {}


def _bootstrap_forms() -> None:
    if FORMS:
        return
    FORMS["incident-report"] = FormTemplate(
        id="incident-report",
        name="Incident Report",
        description="Document workplace incidents with follow up actions.",
        fields=[
            FormField(id="incident_date", label="Incident Date", type="date", required=True),
            FormField(id="location", label="Location", type="text", required=True),
            FormField(id="description", label="Description", type="textarea", required=True),
            FormField(id="follow_up", label="Follow Up", type="textarea", required=False),
        ],
    )
    FORMS["safety-audit"] = FormTemplate(
        id="safety-audit",
        name="Safety Audit",
        description="Routine audit of safety equipment.",
        fields=[
            FormField(id="auditor", label="Auditor", type="text", required=True),
            FormField(id="audit_date", label="Audit Date", type="date", required=True),
            FormField(id="issues_found", label="Issues Found", type="textarea", required=False),
        ],
    )


_bootstrap_forms()


def reset_state() -> None:
    """Utility used by tests to clear in-memory response and assignment state."""
    FORM_RESPONSES.clear()
    ASSIGNMENTS.clear()


def _calculate_progress(form_id: str, answers: Dict[str, Optional[str]]) -> float:
    template = FORMS.get(form_id)
    if not template:
        raise KeyError(form_id)
    required_fields = [field.id for field in template.fields if field.required]
    if not required_fields:
        return 1.0
    completed = sum(
        1 for field_id in required_fields if answers.get(field_id) not in (None, "")
    )
    return completed / len(required_fields)


def _response_status(progress: float) -> str:
    if progress <= 0:
        return "Not Started"
    if progress < 1:
        return "In Progress"
    return "Complete"


def _ensure_response(response_id: str) -> FormResponse:
    response = FORM_RESPONSES.get(response_id)
    if not response:
        raise HTTPException(status_code=404, detail="Response not found")
    return response


@app.get("/forms")
def list_forms() -> List[Dict[str, object]]:
    return [
        {
            "id": form.id,
            "name": form.name,
            "description": form.description,
            "fields": [asdict(field) for field in form.fields],
        }
        for form in FORMS.values()
    ]


@app.get("/forms/{form_id}")
def get_form(form_id: str) -> Dict[str, object]:
    form = FORMS.get(form_id)
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    return {
        "id": form.id,
        "name": form.name,
        "description": form.description,
        "fields": [asdict(field) for field in form.fields],
    }


@app.post("/form-responses", status_code=201)
def create_form_response(payload: Dict[str, object]) -> Dict[str, object]:
    form_id = payload.get("form_id")
    user_id = payload.get("user_id")
    if not isinstance(form_id, str) or form_id not in FORMS:
        raise HTTPException(status_code=404, detail="Form not found")
    response_id = f"resp-{len(FORM_RESPONSES) + 1}"
    answers: Dict[str, Optional[str]] = {}
    progress = _calculate_progress(form_id, answers)
    response = FormResponse(
        id=response_id,
        form_id=form_id,
        answers=answers,
        updated_at=datetime.utcnow(),
        status=_response_status(progress),
        progress=progress,
    )
    FORM_RESPONSES[response_id] = response

    if isinstance(user_id, str) and user_id:
        ASSIGNMENTS[response_id] = FormAssignment(
            form_id=form_id,
            user_id=user_id,
            response_id=response_id,
        )

    return response.to_dict()


@app.get("/form-responses/{response_id}")
def get_form_response(response_id: str) -> Dict[str, object]:
    response = _ensure_response(response_id)
    return response.to_dict()


@app.patch("/form-responses/{response_id}")
def patch_form_response(response_id: str, payload: Dict[str, object]) -> Dict[str, object]:
    response = _ensure_response(response_id)
    answers_payload = payload.get("answers") or {}
    if not isinstance(answers_payload, dict):
        raise HTTPException(status_code=400, detail="Invalid answers payload")

    new_answers = {**response.answers, **answers_payload}
    progress = _calculate_progress(response.form_id, new_answers)
    response.answers = new_answers
    response.progress = progress
    response.status = _response_status(progress)
    response.updated_at = datetime.utcnow()
    FORM_RESPONSES[response_id] = response
    return response.to_dict()


@app.post("/forms/{form_id}/assign")
def assign_form(form_id: str, payload: Dict[str, object]) -> Dict[str, str]:
    if form_id not in FORMS:
        raise HTTPException(status_code=404, detail="Form not found")
    user_id = payload.get("user_id")
    if not isinstance(user_id, str) or not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
    response_id = payload.get("response_id")

    if isinstance(response_id, str):
        response = FORM_RESPONSES.get(response_id)
        if not response or response.form_id != form_id:
            raise HTTPException(status_code=404, detail="Response not found for form")
        ASSIGNMENTS[response_id] = FormAssignment(form_id=form_id, user_id=user_id, response_id=response_id)
        return ASSIGNMENTS[response_id].to_dict()

    created = create_form_response({"form_id": form_id})
    assignment = FormAssignment(form_id=form_id, user_id=user_id, response_id=created["id"])
    ASSIGNMENTS[created["id"]] = assignment
    return assignment.to_dict()


@app.get("/users/{user_id}/assignments")
def get_user_assignments(user_id: str) -> List[Dict[str, object]]:
    assignments: List[Dict[str, object]] = []
    for assignment in ASSIGNMENTS.values():
        if assignment.user_id != user_id:
            continue
        response = FORM_RESPONSES.get(assignment.response_id)
        form = FORMS.get(assignment.form_id)
        if not response or not form:
            continue
        assignments.append(
            {
                "form_id": assignment.form_id,
                "form_name": form.name,
                "response_id": response.id,
                "status": response.status,
                "progress": response.progress,
            }
        )
    return assignments


@app.get("/forms/{form_id}/assignments")
def get_form_assignments(form_id: str) -> List[Dict[str, object]]:
    if form_id not in FORMS:
        raise HTTPException(status_code=404, detail="Form not found")
    assignments: List[Dict[str, object]] = []
    for assignment in ASSIGNMENTS.values():
        if assignment.form_id != form_id:
            continue
        response = FORM_RESPONSES.get(assignment.response_id)
        form = FORMS.get(assignment.form_id)
        if not response or not form:
            continue
        assignments.append(
            {
                "form_id": assignment.form_id,
                "form_name": form.name,
                "response_id": response.id,
                "status": response.status,
                "progress": response.progress,
            }
        )
    return assignments
