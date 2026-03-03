"""Tests for PAGE gel calculations.

Validates band migration, spot positioning,
and intensity classification. Spec §6.
"""
import math

import pytest

from backend.engine.protein import Protein
from backend.engine.gel import (
    mobility,
    calculate_1d_bands,
    calculate_2d_spots,
    get_marker_positions,
)
from backend.engine.separation import set_plot_array
from backend.engine.constants import MW_MARKERS


def test_mobility_inverse_log_mw():
    """Higher MW proteins migrate less (lower mobility value)."""
    mob_high = mobility(80000)
    mob_low = mobility(10000)
    assert mob_low > mob_high


def test_mobility_known_values():
    """Mobility matches expected values for marker MWs."""
    # mobility(mw) = 120 * (11.5 - log10(mw))
    for mw in MW_MARKERS:
        expected = 120.0 * (11.5 - math.log10(mw))
        assert abs(mobility(mw) - expected) < 1e-10


def test_1d_bands_subunit_based():
    """1D PAGE shows subunit bands, not native protein bands."""
    # Protein with 2 subunit types
    p = Protein(
        amount=10.0, mol_wt=100000.0,
        no_of_sub1=2, subunit1=60000.0,
        no_of_sub2=1, subunit2=40000.0,
    )
    p.k1 = 125.0
    p.k2 = 10.0
    p.k3 = 10.0 * p.amount / p.k2
    fractions = set_plot_array([p])
    bands = calculate_1d_bands([p], fractions, [63])  # near the peak at 125
    # Should have bands for both subunit types
    subunit_mws = {b["subunit_mw"] for b in bands}
    assert 60000.0 in subunit_mws
    assert 40000.0 in subunit_mws


def test_2d_spot_x_from_isopoint():
    """2D spot X position = (pI - 4.0) * 100."""
    p = Protein(
        amount=10.0, mol_wt=50000.0,
        no_of_sub1=1, subunit1=50000.0,
        isopoint=6.5,
    )
    p.k1 = 125.0
    p.k2 = 10.0
    p.k3 = 10.0 * p.amount / p.k2
    fractions = set_plot_array([p])
    spots = calculate_2d_spots([p], fractions, 63)
    assert len(spots) > 0
    expected_x = (6.5 - 4.0) * 100.0
    assert abs(spots[0]["x"] - expected_x) < 1e-10


def test_marker_positions():
    """MW markers at correct mobility positions."""
    markers = get_marker_positions()
    assert len(markers) == len(MW_MARKERS)
    for (mw, pos), expected_mw in zip(markers, MW_MARKERS):
        assert mw == expected_mw
        assert abs(pos - mobility(expected_mw)) < 1e-10


def test_intensity_classification():
    """Band intensity maps to correct thickness category."""
    # Single protein, all the intensity in one band
    p = Protein(
        amount=10.0, mol_wt=50000.0,
        no_of_sub1=1, subunit1=50000.0,
    )
    p.k1 = 125.0
    p.k2 = 10.0
    p.k3 = 10.0 * p.amount / p.k2
    fractions = set_plot_array([p])
    bands = calculate_1d_bands([p], fractions, [63])
    # Only one protein, so intensity should be ~1.0
    assert len(bands) > 0
    assert bands[0]["intensity"] > 0.9
