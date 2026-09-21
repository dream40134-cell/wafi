"""Use-case orchestration. Knows about domain + the classifier and cache
Protocols, never about FastAPI, HTTP, or any concrete implementation."""
from __future__ import annotations

from wafi.adapters.classifier_protocol import TicketClassifier
from wafi.adapters.idempotency_cache import IdempotencyCache, NullCache
from wafi.domain.entities import Ticket, TriageDecision
from wafi.domain.policy import apply_invariants, default_decision, ticket_cache_key


class TriageService:
    """Constructor-injected with any object satisfying TicketClassifier and,
    optionally, IdempotencyCache. Swap either dependency without touching
    this class — the DI seam required by the architecture rules."""

    def __init__(self, classifier: TicketClassifier, cache: IdempotencyCache | None = None) -> None:
        self._classifier = classifier
        self._cache = cache or NullCache()

    def warm_up(self) -> None:
        self._classifier.warm_up()

    def triage(self, ticket: Ticket) -> TriageDecision:
        key = ticket_cache_key(ticket)

        cached = self._cache.get(key)
        if cached is not None:
            # Re-apply invariants even on a cache hit: defense in depth, so
            # the outage guarantee can never be silently bypassed by a
            # stale cache entry.
            return apply_invariants(ticket, cached)

        try:
            output = self._classifier.classify(ticket)
            decision = TriageDecision(
                team=output.team,
                urgency=output.urgency,
                rationale=f"classified by model (confidence={output.confidence:.2f})",
            )
        except RuntimeError:
            decision = default_decision()

        decision = apply_invariants(ticket, decision)
        self._cache.set(key, decision)
        return decision
