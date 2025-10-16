from __future__ import annotations

from enum import Enum


class FormStatusEnum(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class NotificationType(str, Enum):
    ASSIGNMENT = "assignment"
    STATUS_CHANGE = "status_change"
    MESSAGE = "message"
