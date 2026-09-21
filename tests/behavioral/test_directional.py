"""Behavioural test: DIRECTIONAL.

Rule under test: raising the number of affected users must never move the
urgency verdict DOWN. It may stay the same or go up, never down.
"""
from fastapi.testclient import TestClient

from wafi.api.app import app

_URGENCY_RANK = {"low": 0, "medium": 1, "urgent": 2}


def test_more_affected_users_never_lowers_urgency():
    text = "my monitor has a flickering issue"
    with TestClient(app) as client:
        low_count = client.post("/v1/predict", json={"text": text, "affected_users": 1}).json()
        high_count = client.post("/v1/predict", json={"text": text, "affected_users": 5000}).json()

    low_rank = _URGENCY_RANK[low_count["data"]["urgency"]]
    high_rank = _URGENCY_RANK[high_count["data"]["urgency"]]

    assert high_rank >= low_rank
