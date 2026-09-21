"""EXTENSION STUB — not wired into the service yet.

Suggested extension: cache (ticket_hash -> decision) in Redis for N minutes
so an identical ticket submitted twice (e.g. a retried request) returns the
same decision instead of being re-classified. This gives you a real,
demoable extension AND a reason the compose file has a second service.

To finish it:
1. Add a `redis` dependency to pyproject.toml.
2. Implement get()/set() below using redis.asyncio.
3. Inject an instance into TriageService (constructor param, same DI pattern
   as the classifier) and check it before calling the classifier.
4. Write one behavioural test: submitting the same ticket twice returns an
   identical trace-independent decision, and a unit test with a fake cache.
5. Document the decision (why Redis, TTL choice) in DECISIONS.md.
"""
from __future__ import annotations

from typing import Protocol

from wafi.domain.entities import TriageDecision


class IdempotencyCache(Protocol):
    def get(self, key: str) -> TriageDecision | None: ...
    def set(self, key: str, decision: TriageDecision, ttl_seconds: int = 300) -> None: ...


class NullCache:
    """No-op default so the service works unchanged until the extension is wired in."""

    def get(self, key: str) -> TriageDecision | None:
        return None

    def set(self, key: str, decision: TriageDecision, ttl_seconds: int = 300) -> None:
        return None
