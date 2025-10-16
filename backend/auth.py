from __future__ import annotations

from typing import Optional

from backend.database import Database, User


class AuthError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def authenticate(db: Database, headers: dict[str, str]) -> User:
    user_header = headers.get("X-User-Id")
    if not user_header:
        raise AuthError(401, "Missing X-User-Id header")
    try:
        user_id = int(user_header)
    except ValueError:
        raise AuthError(400, "Invalid X-User-Id header")
    user = db.get_user(user_id)
    if user is None:
        raise AuthError(401, "Unknown user")
    return user
