"""Tests for the PurificationSession state machine.

Validates state transitions and menu enable/disable rules.
Spec §9.
"""
import pytest

from backend.engine.session import PurificationSession
from backend.engine.enums import SessionPhase


def test_initial_state():
    """New session starts in SPLASH phase with pooled=True."""
    session = PurificationSession("test-123")
    assert session.phase == SessionPhase.SPLASH
    assert session.pooled is True
    assert session.has_fractions is False
    assert session.assayed is False


def test_can_separate_when_pooled():
    """Separation is enabled when pooled=True and phase=RUNNING."""
    session = PurificationSession("test-123")
    session.phase = SessionPhase.RUNNING
    session.pooled = True
    assert session.can_separate() is True


def test_cannot_separate_with_fractions():
    """Separation is disabled when pooled=False (fractions not yet pooled)."""
    session = PurificationSession("test-123")
    session.phase = SessionPhase.RUNNING
    session.pooled = False
    assert session.can_separate() is False


def test_can_pool_with_fractions():
    """Pool is enabled when has_fractions=True and not yet pooled."""
    session = PurificationSession("test-123")
    session.has_fractions = True
    session.pooled = False
    assert session.can_pool() is True


def test_dilute_disabled_at_max():
    """Dilute is disabled when over_diluted=True."""
    session = PurificationSession("test-123")
    session.has_fractions = True
    session.over_diluted = True
    assert session.can_dilute() is False


def test_assay_single_use():
    """Assay is disabled after first use per step."""
    session = PurificationSession("test-123")
    session.has_fractions = True
    session.assayed = False
    assert session.can_assay() is True
    session.assayed = True
    assert session.can_assay() is False


# ---------------------------------------------------------------------------
# to_state_dict() banner key tests
# ---------------------------------------------------------------------------

def _make_protein(amount: float = 5.0, activity: int = 4):
    from backend.engine.protein import Protein
    return Protein(amount=amount, original_amount=5.0, activity=activity, original_activity=activity)


def _make_step_record(enrichment: float, enzyme_yield: float):
    from backend.engine.step_record import StepRecord
    return StepRecord(
        step_type="test",
        protein_amount=10.0,
        enzyme_units=500.0,
        enzyme_yield=enzyme_yield,
        enrichment=enrichment,
        cost_per_unit=0.5,
    )


def test_state_dict_success_message():
    """to_state_dict() includes success_message when FINISHED and success criteria met."""
    session = PurificationSession("s1")
    session.phase = SessionPhase.FINISHED
    session.enzyme_index = 0
    session.proteins = [_make_protein(amount=5.0, activity=4)]
    session.account.records = [
        _make_step_record(1.0, 100.0),   # initial
        _make_step_record(15.0, 80.0),   # success: enrichment=15>=10, yield=80>=5
    ]
    state = session.to_state_dict()
    assert "success_message" in state, "success_message missing from FINISHED+success state"
    assert "failure_message" not in state


def test_state_dict_failure_message_enzyme_lost():
    """to_state_dict() includes failure_message when FINISHED and enzyme is gone."""
    session = PurificationSession("s2")
    session.phase = SessionPhase.FINISHED
    session.enzyme_index = 0
    session.proteins = [_make_protein(amount=0.0, activity=0)]
    session.account.records = [
        _make_step_record(1.0, 100.0),
        _make_step_record(0.0, 0.0),
    ]
    state = session.to_state_dict()
    assert "failure_message" in state
    assert state["failure_message"] == "You have lost the enzyme!"
    assert "success_message" not in state


def test_state_dict_failure_message_too_many_steps():
    """to_state_dict() includes 'Not finished in time' when FINISHED with 11 records."""
    from backend.engine.constants import MAX_STEPS
    session = PurificationSession("s3")
    session.phase = SessionPhase.FINISHED
    session.enzyme_index = 0
    session.proteins = [_make_protein()]
    # MAX_STEPS == 11: fill exactly 11 records
    session.account.records = [
        _make_step_record(1.0, 100.0) for _ in range(MAX_STEPS)
    ]
    assert len(session.account.records) == MAX_STEPS
    state = session.to_state_dict()
    assert "failure_message" in state
    assert state["failure_message"] == "Not finished in time"
    assert "success_message" not in state


def test_state_dict_no_banner_when_running():
    """to_state_dict() includes neither message when phase is RUNNING."""
    session = PurificationSession("s4")
    session.phase = SessionPhase.RUNNING
    session.enzyme_index = 0
    session.proteins = [_make_protein()]
    session.account.records = [_make_step_record(1.0, 100.0)]
    state = session.to_state_dict()
    assert "success_message" not in state
    assert "failure_message" not in state


def test_state_dict_no_banner_when_splash():
    """to_state_dict() includes neither message when phase is SPLASH."""
    session = PurificationSession("s5")
    # phase defaults to SPLASH, enzyme_index defaults to -1
    state = session.to_state_dict()
    assert "success_message" not in state
    assert "failure_message" not in state
