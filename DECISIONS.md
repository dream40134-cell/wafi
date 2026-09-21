# Engineering Decisions

## 1. Rule-based classifier instead of a trained ML model
**Decision:** `KeywordClassifier` uses keyword matching, not scikit-learn/XGBoost.
**Rationale:** The spec explicitly allows "even a simple rule-based policy."
For ticket triage, staff need to trust *why* a ticket was routed somewhere —
a keyword match is trivially explainable, while a trained model would need
its own explainability work that the 24-hour window doesn't allow for.
The `TicketClassifier` Protocol means this can be swapped for a real model
later with zero changes to `service/` or `api/`.

## 2. Domain invariant applied as a post-processing step, not inside the classifier
**Decision:** `apply_invariants()` runs *after* `TriageService` gets the
classifier's output, in `domain/policy.py`, and can only escalate — never
downgrade.
**Rationale:** If the outage-detection rule lived inside the classifier, a
future model swap could silently drop it. Keeping it as a separate, pure,
tested domain function means the guarantee survives any adapter change and
is provable with a fast unit test with no API or model involved.

## 3. Health/ready split with readiness driven by real startup state
**Decision:** `/health` always returns 200 if the process is alive; `/ready`
returns 503 until `lifespan()` has finished warm-up.
**Rationale:** Conflating the two causes orchestrators (k8s, compose) to
route traffic to a pod that hasn't finished loading, causing avoidable 500s
on the first requests after a deploy.

## 4. Coverage gate excludes `api/app.py` from the percentage
**Decision:** `pyproject.toml` omits `wafi/api/app.py` from `--cov`.
**Rationale:** That file is wiring/lifecycle code (DI composition root),
best proven by the integration tests that exercise it end-to-end, not by
unit-test line coverage. Excluding it keeps the 80% gate meaningful for the
business-logic layers (`domain`, `service`, `adapters`) instead of being
inflated or deflated by boilerplate.

## 5. Redis added as the compose supporting service, gated on real health
**Decision:** `docker-compose.yml` includes `redis` with a healthcheck, and
`wafi` uses `depends_on: condition: service_healthy`.
**Rationale:** The spec requires a supporting service gated on real health,
not just container start order. Redis was chosen because it's a natural fit
for the planned idempotency-cache extension (see README), so the
infrastructure decision and the extension decision reinforce each other
instead of being two unrelated additions.
