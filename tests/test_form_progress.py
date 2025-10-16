import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import pytest
from fastapi.testclient import TestClient

from backend.app import app, reset_state


client = TestClient(app)


def setup_function() -> None:
    reset_state()


def teardown_function() -> None:
    reset_state()


def test_autosave_progress_persists_across_sessions() -> None:
    assign_response = client.post("/forms/incident-report/assign", json={"user_id": "alice"})
    assert assign_response.status_code == 200
    response_id = assign_response.json()["response_id"]

    patch_payload = {
        "answers": {
            "incident_date": "2024-01-01",
            "location": "Warehouse",
        }
    }
    patch_response = client.patch(f"/form-responses/{response_id}", json=patch_payload)
    assert patch_response.status_code == 200
    patch_json = patch_response.json()
    assert patch_json["status"] == "In Progress"
    assert patch_json["progress"] == pytest.approx(2 / 3, rel=1e-3)

    new_session_client = TestClient(app)
    fetched = new_session_client.get(f"/form-responses/{response_id}")
    assert fetched.status_code == 200
    fetched_json = fetched.json()
    assert fetched_json["answers"]["incident_date"] == "2024-01-01"
    assert fetched_json["answers"]["location"] == "Warehouse"
    assert fetched_json["status"] == "In Progress"

    assignments = new_session_client.get("/users/alice/assignments")
    assert assignments.status_code == 200
    assignment_list = assignments.json()
    assert len(assignment_list) == 1
    assert assignment_list[0]["response_id"] == response_id
    assert assignment_list[0]["status"] == "In Progress"

    completion_patch = {
        "answers": {
            "description": "Minor incident handled on site",
        }
    }
    completed_response = new_session_client.patch(
        f"/form-responses/{response_id}", json=completion_patch
    )
    assert completed_response.status_code == 200
    completed_json = completed_response.json()
    assert completed_json["status"] == "Complete"
    assert completed_json["progress"] == pytest.approx(1.0)

    refreshed_assignments = new_session_client.get("/users/alice/assignments")
    assert refreshed_assignments.status_code == 200
    refreshed = refreshed_assignments.json()
    assert refreshed[0]["status"] == "Complete"


def test_reassignment_keeps_progress() -> None:
    first_assignment = client.post("/forms/safety-audit/assign", json={"user_id": "maria"})
    assert first_assignment.status_code == 200
    response_id = first_assignment.json()["response_id"]

    client.patch(
        f"/form-responses/{response_id}",
        json={"answers": {"auditor": "Maria", "audit_date": "2024-03-10"}},
    )

    reassignment = client.post(
        "/forms/safety-audit/assign",
        json={"user_id": "lee", "response_id": response_id},
    )
    assert reassignment.status_code == 200
    assert reassignment.json()["user_id"] == "lee"

    lee_assignments = client.get("/users/lee/assignments")
    assert lee_assignments.status_code == 200
    lee_assignment = lee_assignments.json()[0]
    assert lee_assignment["response_id"] == response_id
    assert lee_assignment["status"] == "Complete"

    old_assignments = client.get("/users/maria/assignments")
    assert old_assignments.status_code == 200
    assert old_assignments.json() == []
