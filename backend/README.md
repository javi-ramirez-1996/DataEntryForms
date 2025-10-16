# Data Entry Forms Backend

This backend provides REST APIs for ingesting PDF form templates and exposing
normalised metadata that can be consumed by the frontend application. It is
implemented with [FastAPI](https://fastapi.tiangolo.com/) and SQLAlchemy.

## Features

* `POST /forms/upload` – accepts a PDF upload, extracts interactive form fields
  using `PyPDF2`, and persists the resulting template metadata in a database.
* `GET /forms/{form_id}` – retrieves the stored template metadata, including
  field descriptors that the frontend can use to render fillable forms.

## Project Structure

```
backend/
├── app.py              # FastAPI application with REST endpoints
├── database.py         # SQLAlchemy engine/session utilities
├── models/
│   └── forms.py        # ORM model for form templates
├── pdf_ingest.py       # Helpers for parsing PDF form fields
└── README.md           # This document
```

## Prerequisites

* Python 3.10+
* PostgreSQL 13+ (or adjust the `DATABASE_URL` for another database engine)

Install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn[standard] sqlalchemy psycopg2-binary PyPDF2
```

## Configuration

The application reads the database connection string from the `DATABASE_URL`
environment variable. By default it targets a local PostgreSQL instance:

```
postgresql+psycopg2://postgres:postgres@localhost:5432/dataentryforms
```

Create the database and ensure the configured user has privileges to read and
write to it.

## Running the API

```bash
export DATABASE_URL="postgresql+psycopg2://postgres:postgres@localhost:5432/dataentryforms"
uvicorn backend.app:app --reload
```

## Using the API

### Upload a form template

```bash
curl -X POST \
  -F "file=@/path/to/form.pdf" \
  -F "title=Sample Form" \
  http://localhost:8000/forms/upload
```

The response contains the persisted metadata, including the generated form ID.

### Retrieve a stored template

```bash
curl http://localhost:8000/forms/1
```

## Database Migrations

For production systems, consider integrating Alembic migrations. The project
currently relies on SQLAlchemy's `Base.metadata.create_all` to create tables at
startup.
