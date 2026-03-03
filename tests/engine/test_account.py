"""Tests for cost tracking and step records.

Validates cost accumulation, record calculations,
and failure condition detection. Spec §5.
"""
import pytest

from backend.engine.protein import Protein
from backend.engine.account import Account


def _make_proteins():
    """Create a simple 3-protein mixture with enzyme at index 1."""
    return [
        Protein(amount=10.0, original_amount=10.0, activity=0, original_activity=0),
        Protein(amount=5.0, original_amount=5.0, activity=4, original_activity=4),
        Protein(amount=8.0, original_amount=8.0, activity=0, original_activity=0),
    ]


def test_initial_record():
    """Step 0 has yield=100% and enrichment=1.0."""
    proteins = _make_proteins()
    acc = Account()
    rec = acc.get_initial_record(proteins, enzyme_index=1)
    assert rec.enzyme_yield == 100.0
    assert rec.enrichment == 1.0
    assert rec.cost_per_unit == 0.0
    assert rec.protein_amount == 23.0  # 10 + 5 + 8
    assert rec.enzyme_units == 5.0 * 4 * 100.0  # amount * activity * 100


def test_cost_accumulation():
    """Total cost increases by technique cost per step."""
    proteins = _make_proteins()
    acc = Account()
    acc.get_initial_record(proteins, enzyme_index=1)
    acc.add_step("gel_filtration", proteins, enzyme_index=1, cost=5.0)
    assert acc.total_cost == 5.0
    acc.add_step("ion_exchange", proteins, enzyme_index=1, cost=5.0)
    assert acc.total_cost == 10.0


def test_enzyme_units_calculation():
    """enzymeUnits = amount * original_activity * 100."""
    proteins = _make_proteins()
    acc = Account()
    rec = acc.get_initial_record(proteins, enzyme_index=1)
    # enzyme: amount=5.0, activity=4 -> 5.0 * 4 * 100 = 2000
    assert rec.enzyme_units == 2000.0


def test_failure_enzyme_lost():
    """Failure triggered when enzymeUnits < 0.01."""
    proteins = _make_proteins()
    proteins[1].amount = 0.0  # enzyme lost
    proteins[1].activity = 0
    acc = Account()
    acc.get_initial_record(proteins, enzyme_index=1)
    result = acc.check_failure(proteins, enzyme_index=1)
    assert result == "You have lost the enzyme!"


def test_failure_too_many_steps():
    """Failure triggered at step 11."""
    proteins = _make_proteins()
    acc = Account()
    acc.get_initial_record(proteins, enzyme_index=1)
    # Add 10 more records to reach 11 total
    for i in range(10):
        acc.add_step("test", proteins, enzyme_index=1, cost=0.0)
    assert len(acc.records) == 11
    result = acc.check_failure(proteins, enzyme_index=1)
    assert result == "Not finished in time"


def test_failure_cost_too_high():
    """Failure triggered when costPerUnit > 1000."""
    proteins = _make_proteins()
    # Make enzyme tiny so cost_per_unit is huge
    proteins[1].amount = 0.001
    acc = Account()
    acc.get_initial_record(proteins, enzyme_index=1)
    acc.add_step("expensive", proteins, enzyme_index=1, cost=500.0)
    result = acc.check_failure(proteins, enzyme_index=1)
    assert result == "Cost is too high!"
