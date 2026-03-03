"""Protein database manager - charge calculations, isoelectric point, mixture operations."""
import math

from .protein import Protein
from .constants import *


def neg_charge(ph: float, pk: float) -> float:
    """Negative charge contribution using Henderson-Hasselbalch. Spec 2.2."""
    z = 10.0 ** (ph - pk)
    return -z / (1.0 + z)


def pos_charge(ph: float, pk: float) -> float:
    """Positive charge contribution using Henderson-Hasselbalch. Spec 2.2."""
    z = 10.0 ** (ph - pk)
    return 1.0 / (1.0 + z)


def calculate_charge(protein: Protein, ph: float) -> float:
    """Net charge of a protein at given pH. Spec 2.2."""
    charges = protein.charges
    z = charges[0] * neg_charge(ph, PKA_ASP)
    z += charges[1] * neg_charge(ph, PKA_GLU)
    z += abs(charges[2]) * pos_charge(ph, PKA_HIS)
    z += charges[3] * pos_charge(ph, PKA_LYS)
    z += charges[4]  # ARG: always +1 per residue
    z += charges[5] * neg_charge(ph, PKA_TYR)
    z += charges[6] * neg_charge(ph, PKA_CYS)
    z += protein.chains * neg_charge(ph, PKA_C_TERMINUS)
    z += protein.chains * pos_charge(ph, PKA_N_TERMINUS)
    return z


def calculate_isoelectric_point(protein: Protein) -> float:
    """Three-pass iterative search to find pI where charge = 0. Spec 2.3."""
    ph = 7.0
    charge = calculate_charge(protein, ph)
    if charge > 0.0:
        while charge > 0.0:
            ph += 1.0
            charge = calculate_charge(protein, ph)
        while charge < 0.0:
            ph -= 0.1
            charge = calculate_charge(protein, ph)
        while charge > 0.0:
            ph += 0.01
            charge = calculate_charge(protein, ph)
    else:
        while charge < 0.0:
            ph -= 1.0
            charge = calculate_charge(protein, ph)
        while charge > 0.0:
            ph += 0.1
            charge = calculate_charge(protein, ph)
        while charge < 0.0:
            ph -= 0.01
            charge = calculate_charge(protein, ph)
    return ph


def initialize_proteins(proteins: list[Protein]) -> None:
    """Compute isoelectric points for all proteins."""
    for protein in proteins:
        protein.isopoint = calculate_isoelectric_point(protein)
