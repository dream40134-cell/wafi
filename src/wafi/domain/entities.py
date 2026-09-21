"""Pure domain entities. No I/O, no framework imports, no external deps."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Team(StrEnum):
    NETWORK = "network"
    HARDWARE = "hardware"
    SOFTWARE = "software"
    ACCOUNTS = "accounts"
    GENERAL = "general"


class Urgency(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    URGENT = "urgent"

    @property
    def rank(self) -> int:
        return {"low": 0, "medium": 1, "urgent": 2}[self.value]


@dataclass(frozen=True)
class Ticket:
    """Input value object. Immutable — a ticket is a fact, not mutable state."""

    text: str
    affected_users: int = 1
    reporter_department: str | None = None


@dataclass(frozen=True)
class TriageDecision:
    """Output value object returned by the service layer."""

    team: Team
    urgency: Urgency
    rationale: str
