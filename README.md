# DataEntryForms

Software to make forms with fillable fields and stores copies to be worked on and to report on.

## Backend

The backend is a lightweight Python service that exposes form-response APIs plus collaborative messaging. It ships with a minimal HTTP server (`backend/server.py`) built on the standard library so no third-party dependencies are required.

### Features

- Endpoints for creating and updating form responses, including assignment and status management.
- A messaging module (`backend/chat/`) that stores threaded comments tied to each form response (`POST /form-responses/{id}/messages`).
- Real-time style delivery through the in-memory `ConnectionManager`, which queues chat events for WebSocket adapters and powers notification refresh logic.
- A notification service (`backend/notifications.py`) that records assignment, status, and message events for email or in-app consumption.

### Running the backend

```bash
python -m backend.server
```

Requests must include an `X-User-Id` header corresponding to an existing user in the in-memory database.

## Frontend

A lightweight web UI (`frontend/index.html`) demonstrates how to:

- Show form details alongside a discussion thread.
- Connect to the chat event queue for live updates (via WebSocket when paired with a compatible adapter) and poll notification data for badges.

Serve the file with any static web server and ensure it can reach the backend (default: `http://127.0.0.1:8000`).

## Tests

Automated tests cover chat posting, notification dispatch, and permission checks.

```bash
pytest
```
