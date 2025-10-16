from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import Callable, Dict, List, Optional, Tuple

from backend.auth import AuthError, authenticate
from backend.chat.service import ChatService
from backend.database import Database, FormResponse, Message, get_db
from backend.models import FormStatusEnum
from backend.notifications import NotificationService
from backend.realtime import ConnectionManager


class Response:
    def __init__(self, status_code: int, body: dict[str, object] | list[dict[str, object]] | None = None):
        self.status_code = status_code
        self.body = body

    def json(self) -> dict[str, object] | list[dict[str, object]] | None:
        return self.body


class App:
    def __init__(self, db: Database):
        self.db = db
        self.routes: List[Tuple[str, str, Callable[[dict, dict], Response]]] = []
        self.connections = ConnectionManager()

    def route(self, method: str, path: str):
        def decorator(func: Callable[[dict, dict], Response]):
            self.routes.append((method.upper(), path, func))
            return func

        return decorator

    def handle(self, method: str, path: str, *, headers: Optional[dict[str, str]] = None, body: Optional[dict] = None) -> Response:
        headers = headers or {}
        for registered_method, registered_path, handler in self.routes:
            params = self._match_path(registered_path, path)
            if params is not None and registered_method == method.upper():
                request = {"params": params, "body": body or {}, "headers": headers}
                return handler(request, headers)
        return Response(404, {"detail": "Not found"})

    def _match_path(self, template: str, path: str) -> Optional[Dict[str, int]]:
        template_parts = [part for part in template.strip("/").split("/") if part]
        path_parts = [part for part in path.strip("/").split("/") if part]
        if len(template_parts) != len(path_parts):
            return None
        params: Dict[str, int] = {}
        for template_part, path_part in zip(template_parts, path_parts):
            if template_part.startswith("{") and template_part.endswith("}"):
                key = template_part.strip("{}");
                params[key] = int(path_part)
            elif template_part != path_part:
                return None
        return params


def serialize_form(form: FormResponse) -> dict[str, object]:
    return {
        "id": form.id,
        "form_id": form.form_id,
        "data": form.data,
        "status": form.status,
        "created_by_id": form.created_by_id,
        "assigned_user_id": form.assigned_user_id,
        "created_at": form.created_at.isoformat(),
        "updated_at": form.updated_at.isoformat(),
    }


def serialize_message(message: Message) -> dict[str, object]:
    return {
        "id": message.id,
        "form_response_id": message.form_response_id,
        "author_id": message.author_id,
        "body": message.body,
        "parent_id": message.parent_id,
        "created_at": message.created_at.isoformat(),
    }


def create_app() -> App:
    db = get_db()
    app = App(db)
    notifier = NotificationService(db)
    connections = app.connections

    @app.route("POST", "/form-responses")
    def create_form_response(request: dict, headers: dict[str, str]) -> Response:
        try:
            current_user = authenticate(db, headers)
        except AuthError as exc:
            return Response(exc.status_code, {"detail": exc.detail})

        payload = request["body"]
        form = db.add_form_response(payload["form_id"], payload.get("data", {}), current_user.id)
        return Response(201, serialize_form(form))

    @app.route("GET", "/form-responses/{form_response_id}")
    def get_form_response(request: dict, headers: dict[str, str]) -> Response:
        params = request["params"]
        form = db.get_form_response(params["form_response_id"])
        if form is None:
            return Response(404, {"detail": "Form response not found"})
        try:
            current_user = authenticate(db, headers)
        except AuthError as exc:
            return Response(exc.status_code, {"detail": exc.detail})
        if not user_has_access(current_user.id, current_user.is_admin, form):
            return Response(403, {"detail": "Not authorized"})
        return Response(200, serialize_form(form))

    @app.route("PATCH", "/form-responses/{form_response_id}")
    def update_form_response(request: dict, headers: dict[str, str]) -> Response:
        params = request["params"]
        form = db.get_form_response(params["form_response_id"])
        if form is None:
            return Response(404, {"detail": "Form response not found"})
        try:
            current_user = authenticate(db, headers)
        except AuthError as exc:
            return Response(exc.status_code, {"detail": exc.detail})
        if form.created_by_id != current_user.id and not current_user.is_admin:
            return Response(403, {"detail": "Not authorized"})

        payload = request["body"]
        if "status" in payload and payload["status"]:
            status_value = payload["status"]
            if status_value not in {item.value for item in FormStatusEnum}:
                return Response(400, {"detail": "Invalid status"})
            form.status = status_value
            notifier.notify_status_change(form, current_user)
        if "assigned_user_id" in payload and payload["assigned_user_id"] is not None:
            assignee = db.get_user(int(payload["assigned_user_id"]))
            if assignee is None:
                return Response(400, {"detail": "Unknown assignee"})
            form.assigned_user_id = assignee.id
            notifier.notify_assignment(form, assignee, current_user)
        db.update_form_response(form)
        return Response(200, serialize_form(form))

    @app.route("POST", "/form-responses/{form_response_id}/messages")
    def post_message(request: dict, headers: dict[str, str]) -> Response:
        params = request["params"]
        form = db.get_form_response(params["form_response_id"])
        if form is None:
            return Response(404, {"detail": "Form response not found"})
        try:
            current_user = authenticate(db, headers)
        except AuthError as exc:
            return Response(exc.status_code, {"detail": exc.detail})
        if not user_has_access(current_user.id, current_user.is_admin, form):
            return Response(403, {"detail": "Not authorized"})

        payload = request["body"]
        chat_service = ChatService(db, notifier, connections)
        message = chat_service.create_message(form.id, current_user.id, payload["body"], payload.get("parent_id"))
        return Response(201, serialize_message(message))

    @app.route("GET", "/form-responses/{form_response_id}/messages")
    def list_messages(request: dict, headers: dict[str, str]) -> Response:
        params = request["params"]
        form = db.get_form_response(params["form_response_id"])
        if form is None:
            return Response(404, {"detail": "Form response not found"})
        try:
            current_user = authenticate(db, headers)
        except AuthError as exc:
            return Response(exc.status_code, {"detail": exc.detail})
        if not user_has_access(current_user.id, current_user.is_admin, form):
            return Response(403, {"detail": "Not authorized"})

        chat_service = ChatService(db, notifier, connections)
        messages = [serialize_message(m) for m in chat_service.list_messages(form.id)]
        return Response(200, messages)

    @app.route("GET", "/notifications")
    def get_notifications(request: dict, headers: dict[str, str]) -> Response:
        try:
            current_user = authenticate(db, headers)
        except AuthError as exc:
            return Response(exc.status_code, {"detail": exc.detail})
        summary = notifier.unread_summary(current_user.id)
        return Response(200, summary)

    @app.route("POST", "/notifications/{notification_id}/read")
    def mark_notification_read(request: dict, headers: dict[str, str]) -> Response:
        try:
            current_user = authenticate(db, headers)
        except AuthError as exc:
            return Response(exc.status_code, {"detail": exc.detail})
        params = request["params"]
        success = db.mark_notification_read(params["notification_id"], current_user.id)
        if not success:
            return Response(404, {"detail": "Notification not found"})
        return Response(204, None)

    return app


def user_has_access(user_id: int, is_admin: bool, form: FormResponse) -> bool:
    return is_admin or form.created_by_id == user_id or form.assigned_user_id == user_id


app = create_app()
