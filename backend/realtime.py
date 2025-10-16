from __future__ import annotations

from collections import defaultdict, deque
from typing import Any, Deque, Dict, List


class ConnectionManager:
    """Simple event queue to emulate WebSocket broadcasts for tests."""

    def __init__(self) -> None:
        self.events: Dict[int, Deque[dict[str, Any]]] = defaultdict(deque)

    def queue_broadcast(self, form_response_id: int, payload: dict[str, Any]) -> None:
        self.events[form_response_id].append(payload)

    def drain_events(self, form_response_id: int) -> List[dict[str, Any]]:
        result: List[dict[str, Any]] = list(self.events[form_response_id])
        self.events[form_response_id].clear()
        return result
