from __future__ import annotations

def test_report_endpoint_returns_data(client, seeded_data):
    form = seeded_data["form"]
    response = client.get(f"/reports/forms/{form.id}", headers={"X-Role": "admin"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["form_name"] == form.name
    assert payload["summary"]["completed_responses"] == 2


def test_report_endpoint_requires_role(client, seeded_data):
    form = seeded_data["form"]
    response = client.get(f"/reports/forms/{form.id}")
    assert response.status_code == 401


def test_export_csv_endpoint(client, seeded_data):
    form = seeded_data["form"]
    response = client.get(
        f"/reports/forms/{form.id}/export",
        params={"format": "csv"},
        headers={"X-Role": "manager"},
    )
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"].lower()


def test_export_pdf_endpoint(client, seeded_data):
    form = seeded_data["form"]
    response = client.get(
        f"/reports/forms/{form.id}/export",
        params={"format": "pdf"},
        headers={"X-Role": "analyst"},
    )
    assert response.status_code == 200
    assert "application/pdf" in response.headers["content-type"].lower()
