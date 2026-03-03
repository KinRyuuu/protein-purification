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
