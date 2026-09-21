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

## 5. Redis as the supporting service, powering a fail-open idempotency-cache extension
**Decision:** `docker-compose.yml` includes `redis` with a healthcheck, `wafi`
waits on `depends_on: condition: service_healthy`, and `TriageService` is
constructor-injected with an `IdempotencyCache` (`RedisIdempotencyCache` when
the `REDIS_URL` env var is set — see `app.py::_build_cache` — `NullCache`
otherwise). An identical ticket (same text + affected_users, hashed in
`domain/policy.py::ticket_cache_key`) submitted twice within the TTL returns
the same decision without re-classifying it. Cache reads/writes fail open
(log + no-op) rather than raising, so a Redis outage degrades to "always
re-classify," never to a 500.
**Rationale:** This satisfies both the supporting-service requirement (real
health-gating, not just start order) and the "at least one extension"
deliverable with a single coherent piece of infrastructure, instead of two
unrelated additions. Fail-open was chosen deliberately: a caching layer is
an optimisation, and an optimisation that can take the core service down
with it is a design bug, not a feature. The cache key lives in the domain
layer (not the adapter) because "what makes two tickets the same request"
is a business rule, not an infrastructure detail.
Tested in `tests/unit/test_triage_service_cache.py` (service-level: a second
identical ticket is served from cache without calling the classifier again,
and invariants are still re-applied on a cache hit) and
`tests/behavioral/test_idempotency_cache.py` (the Redis adapter itself,
against `fakeredis` — no live Redis server required in CI — including the
fail-open path when the client raises).
