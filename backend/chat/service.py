from __future__ import annotations

from typing import List

from backend.chat.models import Message
from backend.database import Database
from backend.notifications import NotificationService
from backend.realtime import ConnectionManager


class ChatService:
    def __init__(
        self,
        db: Database,
        notifier: NotificationService,
        connections: ConnectionManager,
    ) -> None:
        self.db = db
        self.notifier = notifier
        self.connections = connections

    def create_message(self, form_response_id: int, author_id: int, body: str, parent_id: int | None = None) -> Message:
        message = self.db.add_message(form_response_id, author_id, body, parent_id)
        self.notifier.notify_message(message)
        self.connections.queue_broadcast(
            form_response_id,
            {
                "event": "message_created",
                "message": {
                    "id": message.id,
                    "form_response_id": message.form_response_id,
                    "author_id": message.author_id,
                    "body": message.body,
                    "parent_id": message.parent_id,
                    "created_at": message.created_at.isoformat(),
                },
            },
        )
        return message

    def list_messages(self, form_response_id: int) -> List[Message]:
        return sorted(self.db.list_messages(form_response_id), key=lambda m: m.created_at)
