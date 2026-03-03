"""PAGE gel electrophoresis band/spot calculations. Spec Section 6."""
import math

from .protein import Protein
from .constants import MW_MARKERS


def mobility(mw: float) -> float:
    """Band migration distance by molecular weight. Spec 6.1."""
    return 120.0 * (11.5 - math.log10(mw))


def calculate_1d_bands(proteins: list[Protein], fractions: list[list[float]],
                       selected_fractions: list[int]) -> list[dict]:
    """Compute 1D SDS-PAGE band positions and intensities. Spec 6.1."""
    bands: list[dict] = []

    for lane, frac_num in enumerate(selected_fractions):
        # Compute total protein in this fraction
        total_in_fraction = 0.0
        for p_idx, p in enumerate(proteins):
            protein_idx = p_idx + 1  # 1-based indexing in fractions
            amount_in_frac = fractions[2 * frac_num - 1][protein_idx] + fractions[2 * frac_num][protein_idx]
            total_in_fraction += amount_in_frac

        if total_in_fraction <= 0.0:
            continue

        for p_idx, p in enumerate(proteins):
            protein_idx = p_idx + 1
            amount_in_frac = fractions[2 * frac_num - 1][protein_idx] + fractions[2 * frac_num][protein_idx]
            if amount_in_frac <= 0.0:
                continue

            intensity = amount_in_frac / total_in_fraction

            for subunit_mw, count in p.subunit_mws:
                bands.append({
                    "lane": lane,
                    "position": mobility(subunit_mw),
                    "intensity": intensity,
                    "protein_index": p_idx,
                    "subunit_mw": subunit_mw,
                })

    return bands


def calculate_2d_spots(proteins: list[Protein], fractions: list[list[float]],
                       fraction: int) -> list[dict]:
    """Compute 2D PAGE spot positions and intensities. Spec 6.2."""
    spots: list[dict] = []

    # Total protein in this fraction
    total_in_fraction = 0.0
    for p_idx, p in enumerate(proteins):
        protein_idx = p_idx + 1
        amount_in_frac = fractions[2 * fraction - 1][protein_idx] + fractions[2 * fraction][protein_idx]
        total_in_fraction += amount_in_frac

    if total_in_fraction <= 0.0:
        return spots

    for p_idx, p in enumerate(proteins):
        protein_idx = p_idx + 1
        amount_in_frac = fractions[2 * fraction - 1][protein_idx] + fractions[2 * fraction][protein_idx]
        if amount_in_frac <= 0.0:
            continue

        intensity = amount_in_frac / total_in_fraction

        for subunit_mw, count in p.subunit_mws:
            x = (p.isopoint - 4.0) * 100.0
            y = mobility(subunit_mw)
            spots.append({
                "x": x,
                "y": y,
                "intensity": intensity,
                "protein_index": p_idx,
            })

    return spots


def get_marker_positions() -> list[tuple[int, float]]:
    """MW marker positions for gel display. Spec 6.1."""
    return [(mw, mobility(mw)) for mw in MW_MARKERS]
