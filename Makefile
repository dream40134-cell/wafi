.PHONY: install test lint image smoke

IMAGE_NAME ?= wafi
IMAGE_TAG ?= local

install:
	pip install -e ".[dev]"

lint:
	ruff check src tests
	mypy src
	lint-imports

test:
	pytest tests/unit tests/integration tests/behavioral

test-fast:
	pytest tests/unit tests/behavioral -q

image:
	docker build -t $(IMAGE_NAME):$(IMAGE_TAG) .

smoke: image
	docker run -d --rm --name wafi-smoke -p 8000:8000 $(IMAGE_NAME):$(IMAGE_TAG)
	@echo "waiting for /ready ..."
	@for i in $$(seq 1 15); do \
		curl -sf http://localhost:8000/ready && break || sleep 1; \
	done
	curl -sf http://localhost:8000/ready || (docker logs wafi-smoke; docker stop wafi-smoke; exit 1)
	curl -sf -X POST http://localhost:8000/v1/predict -H "Content-Type: application/json" \
		-d '{"text": "smoke test ticket, vpn not connecting"}' || (docker logs wafi-smoke; docker stop wafi-smoke; exit 1)
	docker stop wafi-smoke
	@echo "smoke test passed"
