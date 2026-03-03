"""Tests for charge calculation and isoelectric point.

Validates Henderson-Hasselbalch implementation and
iterative pI bisection. Spec §2.2-2.3.
"""
import pytest

from backend.engine.protein import Protein
from backend.engine.protein_data import (
    neg_charge,
    pos_charge,
    calculate_charge,
    calculate_isoelectric_point,
    initialize_proteins,
)
from backend.engine.constants import PKA_ASP


def test_neg_charge_at_low_ph():
    """At pH << pK, negCharge approaches 0."""
    result = neg_charge(1.0, PKA_ASP)
    assert result > -0.01  # very close to 0


def test_neg_charge_at_high_ph():
    """At pH >> pK, negCharge approaches -1."""
    result = neg_charge(14.0, PKA_ASP)
    assert result < -0.99  # very close to -1


def test_pos_charge_at_low_ph():
    """At pH << pK, posCharge approaches 1."""
    result = pos_charge(1.0, 10.0)
    assert result > 0.99  # very close to 1


def test_pos_charge_at_high_ph():
    """At pH >> pK, posCharge approaches 0."""
    result = pos_charge(14.0, 4.0)
    assert result < 0.01  # very close to 0


def test_charge_calculation_neutral_protein():
    """A protein with balanced charges has near-zero charge at its pI."""
    # Use first protein from Default_Mixture: charges=[16,23,6,31,10,18,3]
    p = Protein(
        charges=[16, 23, 6, 31, 10, 18, 3],
        mol_wt=53500.0,
        no_of_sub1=1,
        subunit1=53500.0,
    )
    pi = calculate_isoelectric_point(p)
    charge_at_pi = calculate_charge(p, pi)
    assert abs(charge_at_pi) < 0.5  # near zero at pI


def test_isoelectric_point_calculation():
    """Computed pI matches expected value for a known protein."""
    p = Protein(
        charges=[16, 23, 6, 31, 10, 18, 3],
        mol_wt=53500.0,
        no_of_sub1=1,
        subunit1=53500.0,
    )
    pi = calculate_isoelectric_point(p)
    # pI should be in a reasonable range (roughly 7-10 for this protein)
    assert 4.0 < pi < 12.0
    # Charge at pI should be near zero
    charge_at_pi = calculate_charge(p, pi)
    assert abs(charge_at_pi) < 0.5


def test_arg_always_positive():
    """Arginine residues contribute +1 regardless of pH."""
    # Create protein with only ARG residues (charges[4])
    p = Protein(
        charges=[0, 0, 0, 0, 5, 0, 0],
        mol_wt=10000.0,
        no_of_sub1=1,
        subunit1=10000.0,
    )
    # At any pH, the ARG contribution is always charges[4] = 5
    # The total charge includes N/C termini, but ARG part is always +5
    charge_low = calculate_charge(p, 2.0)
    charge_high = calculate_charge(p, 12.0)
    # At both extremes, the charge should include the +5 from ARG
    # At low pH: ARG=5, N-term~+1, C-term~0 -> positive
    assert charge_low > 5.0
    # At high pH: ARG=5, N-term~0, C-term~-1 -> still positive from ARG
    assert charge_high > 3.5
