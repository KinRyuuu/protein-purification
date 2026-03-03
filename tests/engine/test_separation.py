"""Tests for separation techniques.

Validates Gaussian kernel, individual technique algorithms,
and fraction pooling. Spec §4.
"""
import math

import pytest

from backend.engine.protein import Protein
from backend.engine.protein_data import calculate_charge, calculate_isoelectric_point
from backend.engine.separation import (
    gauss,
    set_plot_array,
    ammonium_sulfate,
    heat_treatment,
    gel_filtration,
    deae_salt_elution,
    cm_salt_elution,
    pool_fractions,
)
from backend.engine.enums import GelMatrix
from backend.engine.constants import K2_MIN


def test_gauss_peak_at_k1():
    """Gaussian peak value at fraction=K1 equals K3."""
    # At fraction=K1, exponent=0, so gauss = K3 * exp(0) = K3
    result = gauss(100.0, 10.0, 5.0, 100)
    assert abs(result - 5.0) < 1e-10


def test_gauss_overflow_protection():
    """Returns 0.0 when exponent exceeds 50."""
    # fraction far from K1 -> large exponent
    result = gauss(100.0, 1.0, 5.0, 200)
    assert result == 0.0


def test_gauss_k2_minimum():
    """K2 is clamped to 0.00001 minimum."""
    # K2 = 0 should be clamped to K2_MIN
    result = gauss(100.0, 0.0, 5.0, 100)
    assert abs(result - 5.0) < 1e-10  # at K1, should still equal K3


def test_ammonium_sulfate_solubility():
    """AS precipitation produces correct soluble/insoluble fractions."""
    proteins = [
        Protein(charges=[10, 10, 0, 10, 0, 0, 0], mol_wt=50000.0,
                no_of_sub1=1, subunit1=50000.0, amount=10.0),
        Protein(charges=[30, 30, 0, 5, 0, 0, 0], mol_wt=100000.0,
                no_of_sub1=2, subunit1=50000.0, amount=10.0),
    ]
    result = ammonium_sulfate(proteins, 50.0)
    assert len(result["soluble"]) == 2
    assert len(result["insoluble"]) == 2
    # Each protein should have non-negative soluble and insoluble
    for sol, insol, p in zip(result["soluble"], result["insoluble"], proteins):
        assert sol >= 0.0
        assert insol >= 0.0
        assert abs(sol + insol - p.amount) < 1e-10


def test_heat_treatment_no_denaturation_below_threshold():
    """Proteins below denaturation temp retain full amount."""
    p = Protein(amount=10.0, temp=60.0)
    heat_treatment([p], temperature=40.0, duration=10.0)
    assert p.amount == 10.0  # temp < p.temp -> no denaturation


def test_heat_treatment_denaturation():
    """Proteins above denaturation temp lose amount exponentially."""
    p = Protein(amount=10.0, temp=40.0)
    heat_treatment([p], temperature=60.0, duration=10.0)
    # exponent = (60 - 40) / 200 * 10 = 1.0
    expected = 10.0 * math.exp(-1.0)
    assert abs(p.amount - expected) < 1e-10


def test_gel_filtration_excluded_peak_position():
    """Proteins above excluded MW elute at K1=50."""
    p = Protein(charges=[10, 10, 0, 10, 0, 0, 0], mol_wt=200000.0,
                no_of_sub1=1, subunit1=200000.0, amount=10.0)
    gel_filtration([p], GelMatrix.SEPHADEX_G100)  # excluded=150000
    assert p.k1 == 50.0


def test_gel_filtration_included_peak_position():
    """Proteins below included MW elute at K1=220."""
    p = Protein(charges=[10, 10, 0, 10, 0, 0, 0], mol_wt=2000.0,
                no_of_sub1=1, subunit1=2000.0, amount=10.0)
    gel_filtration([p], GelMatrix.SEPHADEX_G100)  # included=4000
    assert p.k1 == 220.0


def test_gel_filtration_intermediate_position():
    """Proteins within range have log-interpolated K1."""
    p = Protein(charges=[10, 10, 0, 10, 0, 0, 0], mol_wt=50000.0,
                no_of_sub1=1, subunit1=50000.0, amount=10.0)
    gel_filtration([p], GelMatrix.SEPHADEX_G100)
    # Should be between 50 and 220
    assert 50.0 < p.k1 < 220.0


def test_deae_positive_protein_flow_through():
    """Positive proteins don't bind DEAE (K1=40)."""
    # Create a very basic protein with lots of positive charges
    p = Protein(charges=[0, 0, 0, 50, 50, 0, 0], mol_wt=50000.0,
                no_of_sub1=1, subunit1=50000.0, amount=10.0,
                ph1=2.0, ph2=12.0, isopoint=10.0)
    deae_salt_elution([p], start_grad=0.0, end_grad=1.0, ph=7.0, titratable=False)
    assert p.k1 == 40.0  # flow-through


def test_cm_negative_protein_flow_through():
    """Negative proteins don't bind CM (K1=40)."""
    # Protein with lots of negative charges
    p = Protein(charges=[50, 50, 0, 0, 0, 0, 0], mol_wt=50000.0,
                no_of_sub1=1, subunit1=50000.0, amount=10.0,
                ph1=2.0, ph2=12.0, isopoint=4.0)
    cm_salt_elution([p], start_grad=0.0, end_grad=1.0, ph=7.0, titratable=False)
    assert p.k1 == 40.0  # flow-through


def test_pool_fractions_total_recovery():
    """Pooling all fractions recovers ~100% of protein."""
    p = Protein(amount=10.0, mol_wt=50000.0, no_of_sub1=1, subunit1=50000.0)
    p.k1 = 125.0
    p.k2 = 10.0
    p.k3 = 10.0 * 10.0 / 10.0  # = 10.0
    fractions = set_plot_array([p])
    original = p.amount
    pool_fractions([p], fractions, 1, 125)
    # Should recover close to original amount
    assert p.amount > original * 0.95


def test_pool_fractions_partial_recovery():
    """Pooling a subset recovers proportional protein."""
    p = Protein(amount=10.0, mol_wt=50000.0, no_of_sub1=1, subunit1=50000.0)
    p.k1 = 125.0
    p.k2 = 10.0
    p.k3 = 10.0 * 10.0 / 10.0
    fractions = set_plot_array([p])
    pool_fractions([p], fractions, 60, 65)
    # Peak is at 125, pooling 60-65 should get very little
    assert p.amount < 5.0  # much less than original 10
