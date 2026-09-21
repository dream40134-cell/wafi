"""A lightweight, dependency-free rule-based classifier.

The capstone spec explicitly allows "even a simple rule-based policy" instead
of a trained model — this keeps the container small and the decision fully
explainable, which matters for an IT-triage use case where staff will ask
"why did it route here".

Swapping this for a real ML model later means writing a new class that
satisfies TicketClassifier — nothing else in the codebase changes.
"""
from __future__ import annotations

from wafi.adapters.classifier_protocol import ClassifierOutput, TicketClassifier
from wafi.domain.entities import Team, Ticket, Urgency

_TEAM_KEYWORDS: dict[Team, tuple[str, ...]] = {
    Team.NETWORK: ("vpn", "wifi", "internet", "network", "connection", "شبكة", "انترنت"),
    Team.HARDWARE: ("laptop", "printer", "monitor", "keyboard", "device", "جهاز", "طابعة"),
    Team.SOFTWARE: ("software", "app", "application", "install", "update", "error", "برنامج", "تطبيق"),
    Team.ACCOUNTS: ("password", "login", "account", "access", "locked out", "كلمة المرور", "حساب"),
}

_URGENT_HINTS = ("urgent", "asap", "immediately", "critical", "عاجل", "فوري")
_LOW_HINTS = ("question", "how do i", "minor", "when convenient", "سؤال", "بسيط")


class KeywordClassifier:
    """Implements TicketClassifier via keyword matching over ticket text."""

    def __init__(self) -> None:
        self._ready = False

    def warm_up(self) -> None:
        # No model weights to load, but we still enforce the same lifecycle
        # contract every adapter must follow, so swapping in a real model
        # later doesn't change the startup sequence.
        self._ready = True

    def classify(self, ticket: Ticket) -> ClassifierOutput:
        if not self._ready:
            raise RuntimeError("KeywordClassifier.warm_up() was not called before use")

        lowered = ticket.text.lower()

        team = Team.GENERAL
        for candidate_team, keywords in _TEAM_KEYWORDS.items():
            if any(kw in lowered for kw in keywords):
                team = candidate_team
                break

        if any(hint in lowered for hint in _URGENT_HINTS) or ticket.affected_users >= 10:
            urgency = Urgency.URGENT
            confidence = 0.7
        elif any(hint in lowered for hint in _LOW_HINTS):
            urgency = Urgency.LOW
            confidence = 0.6
        else:
            urgency = Urgency.MEDIUM
            confidence = 0.5

        return ClassifierOutput(team=team, urgency=urgency, confidence=confidence)
