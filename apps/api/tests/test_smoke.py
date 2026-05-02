"""Smoke test — proves the test harness works end to end."""
from django.test import Client


def test_healthz() -> None:
    client = Client()
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
