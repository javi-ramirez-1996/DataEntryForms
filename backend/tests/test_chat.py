from __future__ import annotations

def _headers(user_id: int) -> dict[str, str]:
    return {"X-User-Id": str(user_id)}


def test_post_message_creates_notification(client, reset_database, seed_users, seed_form_response):
    payload = {"body": "This is a test message."}

    response = client.post(
        "/form-responses/1/messages",
        json=payload,
        headers=_headers(seed_users["creator"]),
    )

    assert response.status_code == 201
    data = response.json()
    assert data["body"] == payload["body"]
    assert data["author_id"] == seed_users["creator"]

    notifications = [n for n in reset_database.list_notifications(seed_users["assignee"])]
    assert len(notifications) == 1
    assert notifications[0].type == "message"


def test_post_message_forbidden_for_unrelated_user(client, seed_users, seed_form_response):
    payload = {"body": "Unauthorized message."}

    response = client.post(
        "/form-responses/1/messages",
        json=payload,
        headers=_headers(seed_users["observer"]),
    )

    assert response.status_code == 403


def test_status_change_notification(client, reset_database, seed_users, seed_form_response):
    response = client.patch(
        "/form-responses/1",
        json={"status": "completed"},
        headers=_headers(seed_users["creator"]),
    )
    assert response.status_code == 200

    notifications = reset_database.list_notifications(seed_users["assignee"])
    assert any(n.type == "status_change" for n in notifications)


def test_assignment_notification(client, reset_database, seed_users, seed_form_response):
    response = client.patch(
        "/form-responses/1",
        json={"assigned_user_id": seed_users["observer"]},
        headers=_headers(seed_users["creator"]),
    )
    assert response.status_code == 200

    notifications = reset_database.list_notifications(seed_users["observer"])
    assert any(n.type == "assignment" for n in notifications)
