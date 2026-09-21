# Benchmarks

Measured on a local MacBook Pro (Python 3.12.7, Docker Desktop, macOS).

## Image size
```bash
docker build -t wafi:local .
docker images wafi:local --format "{{.Size}}"
```
Result: **239MB** (well under the 500MB spec limit)

## Build time
```bash
time docker build --no-cache -t wafi:local .
```
Result: **29.48s** (real)

## Test suite time
```bash
time make test        # full suite
time make test-fast   # unit + behavioural only, no Docker
```
Full suite (unit + integration + behavioral, with coverage): **3.44s** (real), 30 passed
Fast gate (unit + behavioral only, no coverage): **2.03s** (real), 25 passed — well under the 60s spec limit

## Coverage
```bash
pytest --cov=src/wafi --cov-report=term-missing
```
Result: **92.26%** branch coverage on `domain`, `service`, `adapters` (spec requires ≥80%)

## Container cold-start to /ready
```bash
docker compose up -d
```
Result: service reported `/ready` within ~6 seconds of container start (redis health-gate + wafi startup, observed via `docker compose up` logs)
