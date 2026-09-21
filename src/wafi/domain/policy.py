"""Business rules that must hold no matter what the underlying model predicts.

This is the file the behavioural "invariance" test targets. Keeping the rule
here (pure, dependency-free) means the test never has to spin up the API or
the model adapter to prove the guarantee — it just calls a function.
"""
from __future__ import annotations

import hashlib

from .entities import Team, Ticket, TriageDecision, Urgency

# Phrases that indicate a full service outage. Case-insensitive substring match.
# Keep this list small and explicit — it is a legal/compliance-style guarantee,
# not a fuzzy classifier, so ambiguity here is a bug.
OUTAGE_PHRASES: tuple[str, ...] = (
    "service is down",
    "system is down",
    "everyone is down",
    "outage",
    "cannot access anything",
    "nothing is working",
    "complete outage",
    "down for everyone",
    "الخدمة متوقفة كليا",
    "توقف كامل",
    "لا احد يقدر يدخل",
    "النظام واقع بالكامل",
)


def is_full_outage(ticket: Ticket) -> bool:
    lowered = ticket.text.lower()
    return any(phrase.lower() in lowered for phrase in OUTAGE_PHRASES)


def apply_invariants(ticket: Ticket, decision: TriageDecision) -> TriageDecision:
    """Post-process any model/rule output through mandatory business invariants.

    MANDATORY INVARIANT (from the capstone spec):
    A phrase indicating a full service outage must ALWAYS raise urgency to URGENT,
    regardless of what the underlying classifier said.
    """
    if is_full_outage(ticket) and decision.urgency != Urgency.URGENT:
        return TriageDecision(
            team=decision.team,
            urgency=Urgency.URGENT,
            rationale=f"{decision.rationale} | escalated: full-outage phrase detected",
        )
    return decision


def ticket_cache_key(ticket: Ticket) -> str:
    """Deterministic idempotency key: same text + affected_users always
    produces the same key. Kept in domain because "what makes two tickets
    the same request" is a business rule, not an infra detail."""
    normalized = f"{ticket.text.strip().lower()}|{ticket.affected_users}"
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def default_decision() -> TriageDecision:
    """Fallback decision used when the classifier is unavailable — fails safe
    towards a human, never towards silent low-priority routing."""
    return TriageDecision(
        team=Team.GENERAL,
        urgency=Urgency.MEDIUM,
        rationale="fallback: classifier unavailable, routed to general queue for triage",
    )
