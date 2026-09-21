from __future__ import annotations

import os
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from wafi.adapters.idempotency_cache import IdempotencyCache, NullCache, RedisIdempotencyCache
from wafi.adapters.keyword_classifier import KeywordClassifier
from wafi.api.schemas import (
    ErrorDetail,
    ErrorResponse,
    PredictData,
    PredictRequest,
    PredictResponse,
)
from wafi.domain.entities import Ticket
from wafi.service.triage_service import TriageService

# App-level state. Populated at startup, NEVER at import time — importing
# this module must be side-effect free so tests can import it cheaply.
_state: dict[str, object] = {"ready": False, "service": None}


def _build_cache() -> IdempotencyCache:
    redis_url = os.environ.get("REDIS_URL")
    if redis_url:
        return RedisIdempotencyCache(redis_url=redis_url)
    return NullCache()


@asynccontextmanager
async def lifespan(app: FastAPI):
    service = TriageService(classifier=KeywordClassifier(), cache=_build_cache())
    service.warm_up()
    _state["service"] = service
    _state["ready"] = True
    yield
    _state["ready"] = False


app = FastAPI(title="Wafi — IT Helpdesk Triage", lifespan=lifespan)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    trace_id = str(uuid.uuid4())
    body = ErrorResponse(
        trace_id=trace_id,
        error=ErrorDetail(code="VALIDATION_ERROR", message=str(exc.errors())),
    )
    return JSONResponse(status_code=422, content=body.model_dump())


@app.get("/health")
async def health() -> dict[str, str]:
    # Liveness only: "is the process alive". Never checks dependencies.
    return {"status": "alive"}


@app.get("/ready")
async def ready() -> JSONResponse:
    # Readiness: "can this instance actually serve traffic right now".
    if _state["ready"]:
        return JSONResponse(status_code=200, content={"status": "ready"})
    return JSONResponse(status_code=503, content={"status": "not_ready"})


@app.post("/v1/predict", response_model=PredictResponse)
async def predict(payload: PredictRequest) -> PredictResponse:
    trace_id = str(uuid.uuid4())
    service: TriageService = _state["service"]  # type: ignore[assignment]

    ticket = Ticket(
        text=payload.text,
        affected_users=payload.affected_users,
        reporter_department=payload.reporter_department,
    )
    decision = service.triage(ticket)

    return PredictResponse(
        trace_id=trace_id,
        data=PredictData(
            team=decision.team.value,
            urgency=decision.urgency.value,
            rationale=decision.rationale,
        ),
    )
