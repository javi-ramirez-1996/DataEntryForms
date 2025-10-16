from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from . import FastAPI, HTTPException


@dataclass
class Response:
    status_code: int
    _json: Any

    def json(self) -> Any:
        return self._json


class TestClient:
    """Very small subset of TestClient used for integration tests."""

    def __init__(self, app: FastAPI):
        self.app = app

    def request(self, method: str, path: str, json: Optional[Dict[str, Any]] = None) -> Response:
        try:
            status_code, payload = self.app.handle_request(method, path, json)
            return Response(status_code=status_code, _json=payload)
        except HTTPException as exc:  # propagate API style errors
            return Response(status_code=exc.status_code, _json={"detail": exc.detail})

    def get(self, path: str) -> Response:
        return self.request("GET", path)

    def post(self, path: str, json: Optional[Dict[str, Any]] = None) -> Response:
        return self.request("POST", path, json=json)

    def patch(self, path: str, json: Optional[Dict[str, Any]] = None) -> Response:
        return self.request("PATCH", path, json=json)
