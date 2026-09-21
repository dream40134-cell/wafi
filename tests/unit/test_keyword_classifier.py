import pytest

from wafi.adapters.keyword_classifier import KeywordClassifier
from wafi.domain.entities import Team, Ticket


def test_raises_if_used_before_warm_up():
    clf = KeywordClassifier()
    with pytest.raises(RuntimeError):
        clf.classify(Ticket(text="my vpn is not connecting"))


def test_routes_network_keywords_to_network_team():
    clf = KeywordClassifier()
    clf.warm_up()
    result = clf.classify(Ticket(text="My VPN keeps disconnecting every few minutes"))
    assert result.team == Team.NETWORK


def test_routes_password_keywords_to_accounts_team():
    clf = KeywordClassifier()
    clf.warm_up()
    result = clf.classify(Ticket(text="I forgot my password and I'm locked out"))
    assert result.team == Team.ACCOUNTS
