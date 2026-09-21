# Benchmarks

Fill these in with numbers from your own machine/CI run — do not copy these
placeholder values into your submission.

## Image size
```bash
docker build -t wafi:local .
docker images wafi:local --format "{{.Size}}"
```
Result: `TODO`

## Build time
```bash
time docker build --no-cache -t wafi:local .
```
Result: `TODO`

## Test suite time
```bash
time make test        # full suite
time make test-fast   # unit + behavioural only, no Docker
```
Full suite: `TODO`
Fast gate: `TODO` (must be ≤ 60s per the spec)

## Coverage
```bash
pytest --cov=src/wafi --cov-report=term-missing
```
Result: `TODO`% branch coverage on `domain`, `service`, `adapters`

## Container cold-start to /ready
```bash
docker compose up -d
time (until curl -sf http://localhost:8000/ready; do sleep 0.2; done)
```
Result: `TODO`
