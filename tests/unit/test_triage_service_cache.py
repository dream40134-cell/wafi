from wafi.adapters.classifier_protocol import ClassifierOutput
from wafi.domain.entities import Team, Ticket, TriageDecision, Urgency
from wafi.service.triage_service import TriageService


class _CountingClassifier:
    """Test double that counts how many times classify() was actually called,
    so we can prove a cache hit skips the classifier entirely."""

    def __init__(self) -> None:
        self.calls = 0

    def warm_up(self) -> None:
        pass

    def classify(self, ticket: Ticket) -> ClassifierOutput:
        self.calls += 1
        return ClassifierOutput(team=Team.NETWORK, urgency=Urgency.MEDIUM, confidence=0.5)


class _InMemoryCache:
    def __init__(self) -> None:
        self._store: dict[str, TriageDecision] = {}

    def get(self, key: str) -> TriageDecision | None:
        return self._store.get(key)

    def set(self, key: str, decision: TriageDecision, ttl_seconds: int = 300) -> None:
        self._store[key] = decision


def test_second_identical_ticket_is_served_from_cache_not_reclassified():
    classifier = _CountingClassifier()
    service = TriageService(classifier=classifier, cache=_InMemoryCache())
    service.warm_up()

    ticket = Ticket(text="my vpn keeps dropping every few minutes")

    first = service.triage(ticket)
    second = service.triage(ticket)

    assert classifier.calls == 1  # classifier only ran once
    assert first == second


def test_different_tickets_both_hit_the_classifier():
    classifier = _CountingClassifier()
    service = TriageService(classifier=classifier, cache=_InMemoryCache())
    service.warm_up()

    service.triage(Ticket(text="my vpn keeps dropping"))
    service.triage(Ticket(text="my printer is jammed"))

    assert classifier.calls == 2


def test_cache_hit_still_gets_invariants_reapplied():
    """A cached decision must still be escalated if the (identical) ticket
    text matches the outage invariant — defense in depth against a stale
    or manually-seeded cache entry."""
    classifier = _CountingClassifier()
    cache = _InMemoryCache()
    service = TriageService(classifier=classifier, cache=cache)
    service.warm_up()

    ticket = Ticket(text="complete outage, the whole system is down for everyone")
    first = service.triage(ticket)
    assert first.urgency == Urgency.URGENT

    second = service.triage(ticket)
    assert second.urgency == Urgency.URGENT
    assert classifier.calls == 1
