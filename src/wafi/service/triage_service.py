"""Use-case orchestration. Knows about domain + the classifier Protocol,
never about FastAPI, HTTP, or any concrete model implementation."""
from __future__ import annotations

from wafi.adapters.classifier_protocol import TicketClassifier
from wafi.domain.entities import Ticket, TriageDecision
from wafi.domain.policy import apply_invariants, default_decision


class TriageService:
    """Constructor-injected with any object satisfying TicketClassifier.
    This is the dependency-injection seam required by the architecture rules."""

    def __init__(self, classifier: TicketClassifier) -> None:
        self._classifier = classifier

    def warm_up(self) -> None:
        self._classifier.warm_up()

    def triage(self, ticket: Ticket) -> TriageDecision:
        try:
            output = self._classifier.classify(ticket)
            decision = TriageDecision(
                team=output.team,
                urgency=output.urgency,
                rationale=f"classified by model (confidence={output.confidence:.2f})",
            )
        except RuntimeError:
            decision = default_decision()

        # Mandatory business invariant applied AFTER the model, so it can
        # never be silently bypassed by a bad model update.
        return apply_invariants(ticket, decision)
