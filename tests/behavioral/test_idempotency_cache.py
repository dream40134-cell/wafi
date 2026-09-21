"""Behavioural test for the extension: a RedisIdempotencyCache, backed by an
in-memory fake Redis (fakeredis), round-trips a decision correctly and fails
open when the underlying client errors."""
import fakeredis
import pytest

from wafi.adapters.idempotency_cache import RedisIdempotencyCache
from wafi.domain.entities import Team, TriageDecision, Urgency


@pytest.fixture
def cache() -> RedisIdempotencyCache:
    fake_client = fakeredis.FakeStrictRedis()
    return RedisIdempotencyCache(client=fake_client)


def test_set_then_get_round_trips_the_decision(cache: RedisIdempotencyCache):
    decision = TriageDecision(team=Team.NETWORK, urgency=Urgency.MEDIUM, rationale="classified")

    cache.set("some-key", decision)
    result = cache.get("some-key")

    assert result is not None
    assert result.team == Team.NETWORK
    assert result.urgency == Urgency.MEDIUM
    assert "served from idempotency cache" in result.rationale


def test_get_on_missing_key_returns_none(cache: RedisIdempotencyCache):
    assert cache.get("never-set") is None


def test_get_fails_open_on_client_error():
    """If the Redis client raises (connection lost, timeout, etc.), get()
    must return None instead of propagating — a cache outage must never take
    ticket triage down with it."""

    class _BrokenClient:
        def get(self, key: str):
            raise ConnectionError("redis is unreachable")

    broken_cache = RedisIdempotencyCache(client=_BrokenClient())
    assert broken_cache.get("any-key") is None
