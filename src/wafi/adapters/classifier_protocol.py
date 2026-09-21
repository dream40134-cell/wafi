"""The swappable model interface. Service layer depends on this Protocol only —
never on a concrete implementation. Swap KeywordClassifier for an XGBoost or
sklearn-backed adapter later without touching service/ or api/."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from wafi.domain.entities import Team, Ticket, Urgency


@dataclass(frozen=True)
class ClassifierOutput:
    team: Team
    urgency: Urgency
    confidence: float


class TicketClassifier(Protocol):
    def classify(self, ticket: Ticket) -> ClassifierOutput: ...

    def warm_up(self) -> None:
        """Called once at service startup. Must never be called at import time."""
        ...
