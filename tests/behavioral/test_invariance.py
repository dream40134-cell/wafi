"""Behavioural test: INVARIANCE.

This is the test the capstone grading rubric cares about most: it proves
that a specific business rule holds against the REAL running service
(real API, real classifier, real domain policy wired together) — not a mock.

Rule under test (from the spec):
"A phrase indicating full service outage must always raise the urgency level."
"""
import pytest
from fastapi.testclient import TestClient

from wafi.api.app import app

OUTAGE_TICKETS = [
    "The whole system is down for everyone, complete outage",
    "Nothing is working, total outage since this morning",
    "النظام واقع بالكامل ولا احد يقدر يدخل من الصباح",
    "توقف كامل للخدمة على جميع الفروع",
]


@pytest.mark.parametrize("ticket_text", OUTAGE_TICKETS)
def test_outage_phrase_always_forces_urgent(ticket_text: str):
    with TestClient(app) as client:
        resp = client.post("/v1/predict", json={"text": ticket_text})
        assert resp.status_code == 200
        assert resp.json()["data"]["urgency"] == "urgent"


def test_outage_phrase_forces_urgent_even_with_low_urgency_hint():
    """Directional/invariance combined case: the ticket ALSO contains a
    low-priority hint word ("question") — the outage rule must still win."""
    text = "question: is it normal that the whole system is down for everyone?"
    with TestClient(app) as client:
        resp = client.post("/v1/predict", json={"text": text})
        assert resp.json()["data"]["urgency"] == "urgent"
