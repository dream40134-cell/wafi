"""Idempotency cache — the capstone "extension".

An identical ticket (same text + affected_users) submitted twice within the
TTL window returns the same decision instead of being re-classified. Useful
for retried requests (e.g. a flaky client) so the client always gets a
consistent answer.

Design decisions (see DECISIONS.md):
- Fail-open: if Redis is unreachable, get()/set() swallow the error and
  behave as a cache miss/no-op. A caching layer going down must never take
  the actual triage service down with it.
- redis-py's client only opens a connection on the first real command, so
  building a RedisIdempotencyCache at startup never blocks or fails even if
  Redis isn't ready yet.
"""
from __future__ import annotations

import json
import logging
from typing import Protocol

from wafi.domain.entities import Team, TriageDecision, Urgency

logger = logging.getLogger("wafi.adapters.idempotency_cache")


class IdempotencyCache(Protocol):
    def get(self, key: str) -> TriageDecision | None: ...
    def set(self, key: str, decision: TriageDecision, ttl_seconds: int = 300) -> None: ...


class NullCache:
    """No-op default. Used whenever no REDIS_URL is configured, so the
    service works unchanged in environments without Redis (local dev without
    Docker, unit tests, etc.)."""

    def get(self, key: str) -> TriageDecision | None:
        return None

    def set(self, key: str, decision: TriageDecision, ttl_seconds: int = 300) -> None:
        return None


class RedisIdempotencyCache:
    """Redis-backed implementation of IdempotencyCache.

    Accepts either a redis_url (production/compose usage) or a pre-built
    client (test usage, e.g. with fakeredis) — whichever is given, exactly
    one must be provided.
    """

    def __init__(self, redis_url: str | None = None, client: object | None = None) -> None:
        if client is not None:
            self._client = client
        else:
            import redis  # local import: keeps this module importable even
            # in environments that only ever use NullCache and never
            # installed redis-py's C extensions.

            self._client = redis.Redis.from_url(
                redis_url, socket_timeout=1, socket_connect_timeout=1
            )

    def get(self, key: str) -> TriageDecision | None:
        try:
            raw = self._client.get(f"wafi:decision:{key}")
        except Exception:  # noqa: BLE001 — fail-open by design, see module docstring
            logger.warning("idempotency cache GET failed, treating as miss", exc_info=True)
            return None

        if raw is None:
            return None

        try:
            payload = json.loads(raw)
            return TriageDecision(
                team=Team(payload["team"]),
                urgency=Urgency(payload["urgency"]),
                rationale=payload["rationale"] + " | served from idempotency cache",
            )
        except (json.JSONDecodeError, KeyError, ValueError):
            logger.warning("idempotency cache returned malformed entry, treating as miss")
            return None

    def set(self, key: str, decision: TriageDecision, ttl_seconds: int = 300) -> None:
        payload = json.dumps(
            {
                "team": decision.team.value,
                "urgency": decision.urgency.value,
                "rationale": decision.rationale,
            }
        )
        try:
            self._client.set(f"wafi:decision:{key}", payload, ex=ttl_seconds)
        except Exception:  # noqa: BLE001 — fail-open by design, see module docstring
            logger.warning("idempotency cache SET failed, decision was not cached", exc_info=True)
