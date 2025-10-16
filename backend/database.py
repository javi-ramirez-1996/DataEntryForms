from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from threading import RLock
from typing import Dict, List, Optional


@dataclass
class User:
    id: int
    email: str
    full_name: str
    is_admin: bool = False


@dataclass
class FormResponse:
    id: int
    form_id: int
    data: Dict[str, object]
    status: str
    created_by_id: int
    assigned_user_id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Message:
    id: int
    form_response_id: int
    author_id: int
    body: str
    parent_id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Notification:
    id: int
    user_id: int
    form_response_id: Optional[int]
    message: str
    type: str
    is_read: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)


class Database:
    def __init__(self) -> None:
        self._lock = RLock()
        self.users: Dict[int, User] = {}
        self.form_responses: Dict[int, FormResponse] = {}
        self.messages: Dict[int, Message] = {}
        self.notifications: Dict[int, Notification] = {}
        self._counters = {"users": 0, "form_responses": 0, "messages": 0, "notifications": 0}

    def _next_id(self, collection: str) -> int:
        with self._lock:
            self._counters[collection] += 1
            return self._counters[collection]

    def add_user(self, email: str, full_name: str, *, is_admin: bool = False) -> User:
        user = User(id=self._next_id("users"), email=email, full_name=full_name, is_admin=is_admin)
        self.users[user.id] = user
        return user

    def get_user(self, user_id: int) -> Optional[User]:
        return self.users.get(user_id)

    def add_form_response(self, form_id: int, data: Dict[str, object], created_by_id: int) -> FormResponse:
        form = FormResponse(
            id=self._next_id("form_responses"),
            form_id=form_id,
            data=data,
            status="open",
            created_by_id=created_by_id,
        )
        self.form_responses[form.id] = form
        return form

    def get_form_response(self, form_response_id: int) -> Optional[FormResponse]:
        return self.form_responses.get(form_response_id)

    def update_form_response(self, form_response: FormResponse) -> None:
        form_response.updated_at = datetime.utcnow()
        self.form_responses[form_response.id] = form_response

    def add_message(
        self,
        form_response_id: int,
        author_id: int,
        body: str,
        parent_id: Optional[int] = None,
    ) -> Message:
        message = Message(
            id=self._next_id("messages"),
            form_response_id=form_response_id,
            author_id=author_id,
            body=body,
            parent_id=parent_id,
        )
        self.messages[message.id] = message
        return message

    def list_messages(self, form_response_id: int) -> List[Message]:
        return [m for m in self.messages.values() if m.form_response_id == form_response_id]

    def add_notification(
        self,
        user_id: int,
        form_response_id: Optional[int],
        message: str,
        notif_type: str,
    ) -> Notification:
        notification = Notification(
            id=self._next_id("notifications"),
            user_id=user_id,
            form_response_id=form_response_id,
            message=message,
            type=notif_type,
        )
        self.notifications[notification.id] = notification
        return notification

    def list_notifications(self, user_id: int) -> List[Notification]:
        return [n for n in self.notifications.values() if n.user_id == user_id]

    def mark_notification_read(self, notification_id: int, user_id: int) -> bool:
        notification = self.notifications.get(notification_id)
        if notification and notification.user_id == user_id:
            notification.is_read = True
            return True
        return False


# Singleton database for application usage
_db_instance = Database()


def get_db() -> Database:
    return _db_instance
"""Database configuration for the backend service.

This module exposes a SQLAlchemy session factory configured for a
PostgreSQL database by default. The connection string can be
customised via the ``DATABASE_URL`` environment variable.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@localhost:5432/dataentryforms",
)

# ``future=True`` enables SQLAlchemy 2.0 style usage while retaining 1.4 compatibility.
engine = create_engine(DATABASE_URL, future=True, echo=False)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, class_=Session)

Base = declarative_base()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations.

    Ensures that transactions are committed if everything succeeds, and rolled
    back on failure. Sessions are automatically closed afterwards.
    """

    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
