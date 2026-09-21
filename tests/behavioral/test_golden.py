"""Behavioural test: GOLDEN REFERENCE.

Loads frozen input/output pairs from golden_cases.json and asserts the live
service still produces them exactly.

IMPORTANT (per the capstone's red-flag rules): if this test fails because a
genuine, reviewed change to the model/rules was made, the golden file may be
regenerated — but ONLY with a note in DECISIONS.md explaining why, and only
as part of a reviewed pull request. Regenerating it just to make CI green is
an automatic fail condition. There is deliberately no `--update-golden`
convenience flag in this repo for that reason.
"""
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from wafi.api.app import app

GOLDEN_PATH = Path(__file__).parent / "golden" / "golden_cases.json"
GOLDEN_CASES = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", GOLDEN_CASES, ids=[c["input"]["text"][:30] for c in GOLDEN_CASES])
def test_matches_golden_reference(case: dict):
    with TestClient(app) as client:
        resp = client.post("/v1/predict", json=case["input"])
        body = resp.json()

    assert body["data"]["team"] == case["expected"]["team"]
    assert body["data"]["urgency"] == case["expected"]["urgency"]
