from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PredictRequest(BaseModel):
    # extra="forbid" -> unknown fields are rejected, per the strict-validation requirement
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1, max_length=5000)
    affected_users: int = Field(default=1, ge=1, le=100_000)
    reporter_department: str | None = Field(default=None, max_length=200)


class PredictData(BaseModel):
    team: str
    urgency: str
    rationale: str


class PredictResponse(BaseModel):
    trace_id: str
    data: PredictData
    error: None = None


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    trace_id: str
    data: None = None
    error: ErrorDetail
