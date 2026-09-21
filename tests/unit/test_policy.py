from wafi.domain.entities import Team, Ticket, TriageDecision, Urgency
from wafi.domain.policy import apply_invariants, is_full_outage


def test_is_full_outage_detects_english_phrase():
    ticket = Ticket(text="The whole system is down for everyone in the office")
    assert is_full_outage(ticket)


def test_is_full_outage_detects_arabic_phrase():
    ticket = Ticket(text="النظام واقع بالكامل ولا احد يقدر يدخل")
    assert is_full_outage(ticket)


def test_is_full_outage_false_for_normal_ticket():
    ticket = Ticket(text="My printer on the 3rd floor is out of paper")
    assert not is_full_outage(ticket)


def test_apply_invariants_escalates_low_to_urgent_on_outage():
    ticket = Ticket(text="complete outage, nothing is working")
    low_decision = TriageDecision(team=Team.NETWORK, urgency=Urgency.LOW, rationale="model said low")

    result = apply_invariants(ticket, low_decision)

    assert result.urgency == Urgency.URGENT


def test_apply_invariants_leaves_non_outage_decision_untouched():
    ticket = Ticket(text="Can someone help me update my printer driver")
    decision = TriageDecision(team=Team.HARDWARE, urgency=Urgency.LOW, rationale="model said low")

    result = apply_invariants(ticket, decision)

    assert result == decision
