# Wafi — IT Helpdesk Ticket Triage

Classifies an incoming IT support ticket into `{team, urgency}` so it can be
routed automatically. Built for the SDA-AIE-113 capstone.

## Quickstart (< 10 minutes)

```bash
git clone <your-repo-url>
cd wafi
make install        # editable install + dev deps
make test           # unit + integration + behavioural, coverage gate 80%
```

## Run the service

```bash
docker compose up --build
```

This starts `wafi` on `http://localhost:8000` alongside a `redis` supporting
service. `wafi` waits for redis to report healthy before starting.

## Try it

```bash
# valid request
curl -X POST http://localhost:8000/v1/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "my vpn keeps dropping every few minutes"}'

# malformed request (unknown field -> 422)
curl -X POST http://localhost:8000/v1/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "hello", "not_a_real_field": true}'

curl http://localhost:8000/health   # liveness
curl http://localhost:8000/ready    # readiness
```

## Architecture

```
src/wafi/
  domain/     pure business rules — no imports from any other layer
  service/    use-case orchestration, depends on domain + the classifier Protocol
  adapters/   concrete classifier(s) + I/O, implement the Protocol via DI
  api/        FastAPI endpoints, wires everything together at startup
```

The layering is enforced automatically by `import-linter` (`make lint`) —
`domain` cannot import from `service`, `adapters`, or `api`; the layers
contract in `pyproject.toml` enforces the full stack order.

The model is swappable: `wafi.adapters.classifier_protocol.TicketClassifier`
is the interface; `KeywordClassifier` is the current implementation, injected
into `TriageService` at startup (`src/wafi/api/app.py`).

## Testing

| Level | Location | What it proves |
|---|---|---|
| Unit | `tests/unit/` | domain policy + classifier logic in isolation |
| Integration | `tests/integration/` | the real FastAPI app, via `TestClient` |
| Behavioural — invariance | `tests/behavioral/test_invariance.py` | an outage phrase **always** forces `urgent` |
| Behavioural — directional | `tests/behavioral/test_directional.py` | more affected users never **lowers** urgency |
| Behavioural — golden | `tests/behavioral/test_golden.py` + `golden/golden_cases.json` | live output matches a frozen reference set |

Fast gate (unit + behavioural, no Docker) finishes in well under 60s:
`make test-fast`.

## Extension (in progress — see `adapters/idempotency_cache.py`)

Redis is already wired into `docker-compose.yml` as the supporting service.
The suggested extension is a request-idempotency cache: an identical ticket
submitted twice returns the same decision instead of being re-classified.
The Protocol and a no-op `NullCache` are scaffolded; wiring it in, adding a
real Redis-backed implementation, and testing it is the remaining work for
the "at least one extension" deliverable.

## Repo docs

- `DECISIONS.md` — five engineering decisions with rationale
- `BENCHMARKS.md` — fill in with numbers from your own machine
