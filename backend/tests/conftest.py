from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from typing import Dict

import pytest

import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend import main as main_module  # noqa: E402
from backend.database import Database, get_db  # noqa: E402


@pytest.fixture(autouse=True)
def reset_database() -> Generator[Database, None, None]:
    db = Database()
    original_db = get_db.__globals__["_db_instance"]
    get_db.__globals__["_db_instance"] = db
    main_module.app = main_module.create_app()
    yield db
    get_db.__globals__["_db_instance"] = original_db
    main_module.app = main_module.create_app()


@pytest.fixture()
def client() -> Generator:
    class Client:
        def request(self, method: str, path: str, json: dict | None = None, headers: Dict[str, str] | None = None):
            return main_module.app.handle(method, path, body=json, headers=headers)

        def post(self, path: str, json: dict | None = None, headers: Dict[str, str] | None = None):
            return self.request("POST", path, json=json, headers=headers)

        def get(self, path: str, headers: Dict[str, str] | None = None):
            return self.request("GET", path, headers=headers)

        def patch(self, path: str, json: dict | None = None, headers: Dict[str, str] | None = None):
            return self.request("PATCH", path, json=json, headers=headers)

    yield Client()


@pytest.fixture()
def seed_users(reset_database: Database) -> Dict[str, int]:
    creator = reset_database.add_user("creator@example.com", "Creator")
    assignee = reset_database.add_user("assignee@example.com", "Assignee")
    observer = reset_database.add_user("observer@example.com", "Observer")
    admin = reset_database.add_user("admin@example.com", "Admin", is_admin=True)
    return {"creator": creator.id, "assignee": assignee.id, "observer": observer.id, "admin": admin.id}


@pytest.fixture()
def seed_form_response(reset_database: Database, seed_users: Dict[str, int]):
    form = reset_database.add_form_response(101, {"field": "value"}, seed_users["creator"])
    form.assigned_user_id = seed_users["assignee"]
    reset_database.update_form_response(form)
    return form
