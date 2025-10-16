# DataEntryForms
Software to make forms with fillable fields and stores copies to be worked on and to report on.

## Reporting Service

This repository now includes a reporting API and dashboard that aggregates form
responses, enforces role-based access control, and provides export utilities.

### Running the API

```bash
uvicorn backend.app.main:app --reload
```

Set `ENABLE_REPORT_SCHEDULER=true` to activate the optional background
scheduler that regenerates report snapshots at the interval defined by
`REPORT_SCHEDULER_INTERVAL` (minutes).

### Running Tests

```bash
pytest
```

### Frontend Dashboard

Open `frontend/reports/index.html` in a browser while the API is running. Use
the controls to enter a form identifier, select an authorized role, and view
aggregated charts and tables. Export buttons download CSV or PDF snapshots via
the API.
