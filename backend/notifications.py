from __future__ import annotations

from typing import Set

from backend.chat.models import Message
from backend.database import Database, FormResponse, Notification, User, get_db
from backend.models import NotificationType


class NotificationService:
    def __init__(self, db: Database) -> None:
        self.db = db

    def notify_assignment(self, form_response: FormResponse, assigned_to: User, triggered_by: User) -> None:
        if assigned_to.id == triggered_by.id:
            return
        self.db.add_notification(
            user_id=assigned_to.id,
            form_response_id=form_response.id,
            message=f"You have been assigned to form response #{form_response.id} by {triggered_by.full_name}.",
            notif_type=NotificationType.ASSIGNMENT.value,
        )

    def notify_status_change(self, form_response: FormResponse, triggered_by: User) -> None:
        recipients: Set[int] = {form_response.created_by_id}
        if form_response.assigned_user_id:
            recipients.add(form_response.assigned_user_id)
        recipients.discard(triggered_by.id)
        for recipient in recipients:
            self.db.add_notification(
                user_id=recipient,
                form_response_id=form_response.id,
                message=f"Form response #{form_response.id} status changed to {form_response.status} by {triggered_by.full_name}.",
                notif_type=NotificationType.STATUS_CHANGE.value,
            )

    def notify_message(self, message: Message) -> None:
        form_response = self.db.get_form_response(message.form_response_id)
        if form_response is None:
            return
        recipients: Set[int] = {form_response.created_by_id}
        if form_response.assigned_user_id:
            recipients.add(form_response.assigned_user_id)
        for prior in self.db.list_messages(form_response.id):
            recipients.add(prior.author_id)
        recipients.discard(message.author_id)
        for recipient in recipients:
            self.db.add_notification(
                user_id=recipient,
                form_response_id=form_response.id,
                message=f"New comment on form response #{form_response.id}.",
                notif_type=NotificationType.MESSAGE.value,
            )

    def unread_summary(self, user_id: int) -> dict[str, object]:
        notifications = sorted(self.db.list_notifications(user_id), key=lambda n: n.created_at, reverse=True)
        unread = sum(1 for n in notifications if not n.is_read)
        return {
            "unread_count": unread,
            "items": [self._serialize_notification(n) for n in notifications],
        }

    def _serialize_notification(self, notification: Notification) -> dict[str, object]:
        return {
            "id": notification.id,
            "message": notification.message,
            "type": notification.type,
            "form_response_id": notification.form_response_id,
            "is_read": notification.is_read,
            "created_at": notification.created_at.isoformat(),
        }
