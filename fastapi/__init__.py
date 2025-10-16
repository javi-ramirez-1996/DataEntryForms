from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple


class HTTPException(Exception):
    """Minimal HTTP exception used by the faux FastAPI implementation."""

    def __init__(self, status_code: int, detail: str | Dict[str, Any] | None = None):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail or ""


@dataclass
class Route:
    path: str
    method: str
    endpoint: Callable[..., Any]
    status_code: int

    def match(self, request_path: str) -> Optional[Dict[str, str]]:
        path_tokens = [segment for segment in self.path.strip("/").split("/") if segment]
        request_tokens = [segment for segment in request_path.strip("/").split("/") if segment]
        if len(path_tokens) != len(request_tokens):
            return None
        params: Dict[str, str] = {}
        for pattern, value in zip(path_tokens, request_tokens):
            if pattern.startswith("{") and pattern.endswith("}"):
                params[pattern[1:-1]] = value
            elif pattern != value:
                return None
        return params


class FastAPI:
    """A very small subset of FastAPI used for testing without external deps."""

    def __init__(self, title: str | None = None):
        self.title = title or ""
        self._routes: List[Route] = []

    def _add_route(self, path: str, method: str, endpoint: Callable[..., Any], status_code: int) -> Callable[..., Any]:
        route = Route(path=path, method=method.upper(), endpoint=endpoint, status_code=status_code)
        self._routes.append(route)
        return endpoint

    def get(self, path: str, *, status_code: int = 200) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            return self._add_route(path, "GET", func, status_code)

        return decorator

    def post(self, path: str, *, status_code: int = 200) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            return self._add_route(path, "POST", func, status_code)

        return decorator

    def patch(self, path: str, *, status_code: int = 200) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            return self._add_route(path, "PATCH", func, status_code)

        return decorator

    def _find_route(self, method: str, path: str) -> Tuple[Route, Dict[str, str]]:
        for route in self._routes:
            if route.method != method.upper():
                continue
            params = route.match(path)
            if params is not None:
                return route, params
        raise HTTPException(status_code=404, detail="Not Found")

    def _build_kwargs(self, endpoint: Callable[..., Any], params: Dict[str, str], body: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        signature = inspect.signature(endpoint)
        kwargs: Dict[str, Any] = {}
        for name in signature.parameters.keys():
            if name == "payload":
                kwargs[name] = body or {}
            elif name in params:
                kwargs[name] = params[name]
            else:
                raise TypeError(f"Unable to resolve parameter '{name}' for endpoint {endpoint.__name__}")
        return kwargs

    def handle_request(self, method: str, path: str, body: Optional[Dict[str, Any]] = None) -> Tuple[int, Any]:
        route, params = self._find_route(method, path)
        kwargs = self._build_kwargs(route.endpoint, params, body)
        result = route.endpoint(**kwargs)
        return route.status_code, result


__all__ = ["FastAPI", "HTTPException"]
