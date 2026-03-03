"""Separation engine implementing all 7 purification techniques.

Each technique computes K1, K2, K3 Gaussian parameters per protein,
then populates the fractions array. Spec Section 4.
"""
import math

from .protein import Protein
from .protein_data import calculate_charge
from .constants import *
from .enums import *


# Gel matrix properties: (excluded_mw, included_mw, hires)
GEL_MATRIX_PROPERTIES: dict[GelMatrix, tuple[float, float, bool]] = {
    GelMatrix.SEPHADEX_G50: (30000, 1500, False),
    GelMatrix.SEPHADEX_G100: (150000, 4000, False),
    GelMatrix.SEPHACRYL_S200HR: (220000, 5500, True),
    GelMatrix.ULTROGEL_ACA54: (70000, 6000, False),
    GelMatrix.ULTROGEL_ACA44: (130000, 12000, False),
    GelMatrix.ULTROGEL_ACA34: (400000, 20000, False),
    GelMatrix.BIOGEL_P60: (60000, 3000, False),
    GelMatrix.BIOGEL_P150: (150000, 15000, False),
    GelMatrix.BIOGEL_P300: (400000, 60000, False),
}


def gauss(k1: float, k2: float, k3: float, fraction: int) -> float:
    """Gaussian peak function with overflow protection. Spec Section 4."""
    if k2 < K2_MIN:
        k2 = K2_MIN
    exponent = ((fraction - k1) / k2) ** 2 / 2.0
    if exponent > 50.0:
        return 0.0
    return k3 * math.exp(-exponent)


def set_plot_array(proteins: list[Protein], num_fractions: int = MAX_FRACTIONS) -> list[list[float]]:
    """Compute fractions[1..250][0..N] from current K1/K2/K3. Spec Section 4."""
    fractions: list[list[float]] = [[]]  # index 0 is dummy

    for fraction in range(1, num_fractions + 1):
        absorbance: list[float] = [0.0]  # index 0 = total

        for p in proteins:
            if p.k2 < K2_MIN:
                p.k2 = K2_MIN
            value = gauss(p.k1, p.k2, p.k3, fraction)
            absorbance.append(value)
            absorbance[0] += value

        fractions.append(absorbance)

    return fractions


def _get_log_szero(protein: Protein) -> float:
    """Compute log of solubility in absence of salt."""
    # negCharges = ASP + GLU + chains (C++ code, not CYS/TYR)
    neg_charges = protein.charges[0] + protein.charges[1] + protein.chains
    mol_rad = (protein.mol_wt * 0.75 / math.pi) ** (1.0 / 3.0)
    mol_area = 4.0 * math.pi * mol_rad ** 2
    return (neg_charges / mol_area) * LOG_SZERO_FACTOR


def _get_salt(protein: Protein) -> float:
    """Salt concentration at which protein elutes from HIC column."""
    log_szero = _get_log_szero(protein)
    return (log_szero - 1.0) / (log_szero / AS_BETA_DIVISOR)


def ammonium_sulfate(proteins: list[Protein], saturation: float) -> dict[str, list[float]]:
    """Ammonium sulfate precipitation. Returns soluble and insoluble amounts. Spec 4.1."""
    soluble: list[float] = []
    insoluble: list[float] = []

    for p in proteins:
        log_szero = _get_log_szero(p)
        if log_szero < 1.0:
            log_szero = 1.0

        beta = log_szero / AS_BETA_DIVISOR
        molarity = saturation * SATURATED_AS_MOLARITY / 100.0
        solubility = 10.0 ** (log_szero - beta * molarity)

        precipitated = REFERENCE_CONCENTRATION - solubility
        if precipitated < 0.0:
            precipitated = 0.0

        insol = precipitated / REFERENCE_CONCENTRATION * p.amount
        sol = p.amount - insol

        insoluble.append(insol)
        soluble.append(sol)

    return {"soluble": soluble, "insoluble": insoluble}


def heat_treatment(proteins: list[Protein], temperature: float, duration: float) -> None:
    """First-order denaturation kinetics. Modifies amounts in-place. Spec 4.2."""
    for p in proteins:
        exponent = (temperature - p.temp) / 200.0 * duration
        if exponent > 0.0:
            if exponent < 50.0:
                p.amount *= math.exp(-exponent)
            else:
                p.amount = 0.0
        if p.amount < 0.0:
            p.amount = 0.0


def gel_filtration(proteins: list[Protein], matrix: GelMatrix) -> list[list[float]]:
    """Gel filtration chromatography. Spec 4.3."""
    excluded, included, hires = GEL_MATRIX_PROPERTIES[matrix]
    startgel = math.log(excluded)
    endgel = math.log(included)
    grad = startgel - endgel

    for p in proteins:
        if p.amount > 0.0:
            if included < p.mol_wt < excluded:
                # Within resolving range
                proteinpos = math.log(p.mol_wt)
                p.k1 = GEL_EXCLUDED_PEAK + (GEL_GRADIENT_RANGE * (startgel - proteinpos) / grad)

                if hires:
                    factor = p.k1 / 150.0
                else:
                    factor = p.k1 / 100.0

                p.k2 = factor * math.sqrt(p.amount)
            else:
                if p.mol_wt >= excluded:
                    # Excluded from gel
                    p.k1 = GEL_EXCLUDED_PEAK
                    p.k2 = 5.0
                if p.mol_wt <= included:
                    # Fully penetrates gel
                    p.k1 = GEL_INCLUDED_PEAK
                    p.k2 = 2.55 * math.sqrt(p.amount)
                # Sharpen if hires
                if hires:
                    p.k2 /= 1.5

            # Minimum width
            if p.k2 < MIN_PEAK_WIDTH:
                p.k2 = MIN_PEAK_WIDTH

            # Height
            p.k3 = 10.0 * p.amount / p.k2
        else:
            p.k3 = 0.0

    return set_plot_array(proteins)


def deae_salt_elution(proteins: list[Protein], start_grad: float, end_grad: float,
                      ph: float, titratable: bool) -> list[list[float]]:
    """DEAE ion exchange with salt gradient. Spec 4.4."""
    grad = end_grad - start_grad

    for p in proteins:
        if p.amount > 0.0:
            # Activity loss from pH
            if ph < p.ph1 or ph > p.ph2:
                p.activity = 0

            charge = calculate_charge(p, ph)

            if charge > 0.0 or (titratable and ph >= 10.0):
                # Positive protein or medium lost charge -> flow-through
                p.k1 = IX_FLOW_THROUGH
                p.k2 = 5.0
            else:
                molar = -charge / DEAE_SALT_SENSITIVITY
                if molar <= start_grad:
                    # Washed off by start of gradient
                    p.k1 = IX_GRADIENT_START
                    p.k2 = 2.0
                elif start_grad >= end_grad:
                    # Inverted gradient -> stuck
                    p.k1 = 1000.0
                    p.k2 = 5.0
                else:
                    # Normal gradient elution
                    p.k1 = IX_GRADIENT_START + (IX_GRADIENT_RANGE * ((molar - start_grad) / grad))
                    p.k2 = math.sqrt(p.amount / grad / 2.0)

            p.k3 = 10.0 * p.amount / p.k2
        else:
            p.k3 = 0.0

    return set_plot_array(proteins)


def deae_ph_elution(proteins: list[Protein], start_grad: float, end_grad: float,
                    ph: float, titratable: bool) -> list[list[float]]:
    """DEAE ion exchange with pH gradient. Spec 4.5."""
    factor = 10.0
    grad = start_grad - end_grad  # decreasing pH for DEAE

    for p in proteins:
        if p.amount != 0.0:
            # Activity loss from pH AND start gradient
            if (ph < p.ph1 or ph > p.ph2 or
                    start_grad < p.ph1 or start_grad > p.ph2):
                p.activity = 0

            isopoint = p.isopoint

            if ph < isopoint or (titratable and ph >= 10.0):
                # Positively charged or column uncharged -> flow-through
                p.k1 = IX_FLOW_THROUGH
                p.k2 = 5.0
            else:
                if isopoint >= start_grad:
                    # Washed off by start of gradient
                    p.k1 = IX_GRADIENT_START
                    p.k2 = 2.0
                elif end_grad >= start_grad:
                    # Inverted gradient -> stuck
                    p.k1 = 1000.0
                    p.k2 = 5.0
                else:
                    # Normal gradient elution
                    p.k1 = IX_GRADIENT_START + (IX_GRADIENT_RANGE * (start_grad - isopoint) / grad)
                    p.k2 = factor * math.sqrt(p.amount / grad / 2.0)

            p.k3 = 10.0 * p.amount / p.k2
        else:
            p.k3 = 0.0

    return set_plot_array(proteins)


def cm_salt_elution(proteins: list[Protein], start_grad: float, end_grad: float,
                    ph: float, titratable: bool) -> list[list[float]]:
    """CM ion exchange with salt gradient. Spec 4.6."""
    grad = end_grad - start_grad

    for p in proteins:
        if p.amount > 0.0:
            # Activity loss from pH
            if ph < p.ph1 or ph > p.ph2:
                p.activity = 0

            charge = calculate_charge(p, ph)

            if charge < 0.0 or (titratable and ph <= 3.0):
                # Negative protein or medium lost charge -> flow-through
                p.k1 = IX_FLOW_THROUGH
                p.k2 = 5.0
            else:
                molar = charge / CM_SALT_SENSITIVITY
                if molar <= start_grad:
                    # Washed off by start of gradient
                    p.k1 = IX_GRADIENT_START
                    p.k2 = 2.0
                elif start_grad >= end_grad:
                    # Inverted gradient -> stuck
                    p.k1 = 1000.0
                    p.k2 = 5.0
                else:
                    # Normal gradient elution
                    p.k1 = IX_GRADIENT_START + (IX_GRADIENT_RANGE * ((molar - start_grad) / grad))
                    p.k2 = math.sqrt(p.amount / grad / 2.0)

            p.k3 = 10.0 * p.amount / p.k2
        else:
            p.k3 = 0.0

    return set_plot_array(proteins)


def cm_ph_elution(proteins: list[Protein], start_grad: float, end_grad: float,
                  ph: float, titratable: bool) -> list[list[float]]:
    """CM ion exchange with pH gradient. Spec 4.7."""
    factor = 10.0
    grad = end_grad - start_grad  # increasing pH for CM

    for p in proteins:
        if p.amount != 0.0:
            # Activity loss from pH AND start gradient
            if (ph < p.ph1 or ph > p.ph2 or
                    start_grad < p.ph1 or start_grad > p.ph2):
                p.activity = 0

            isopoint = p.isopoint

            if ph >= isopoint or (titratable and ph <= 3.0):
                # Negatively charged or column uncharged -> flow-through
                p.k1 = IX_FLOW_THROUGH
                p.k2 = 5.0
            else:
                if isopoint <= start_grad:
                    # Washed off by start of gradient
                    p.k1 = IX_GRADIENT_START
                    p.k2 = 2.0
                elif end_grad <= start_grad:
                    # Inverted gradient -> stuck
                    p.k1 = 1000.0
                    p.k2 = 5.0
                else:
                    # Normal gradient elution
                    p.k1 = IX_GRADIENT_START + (IX_GRADIENT_RANGE * (isopoint - start_grad) / grad)
                    p.k2 = factor * math.sqrt(p.amount / grad / 2.0)

            p.k3 = 10.0 * p.amount / p.k2
        else:
            p.k3 = 0.0

    return set_plot_array(proteins)


def hic(proteins: list[Protein], start_grad: float, end_grad: float,
        medium: HICMedia) -> list[list[float]]:
    """Hydrophobic interaction chromatography. Spec 4.8."""
    if medium == HICMedia.PHENYL_SEPHAROSE:
        factor = HIC_PHENYL_FACTOR
    else:
        factor = HIC_OCTYL_FACTOR

    grad = start_grad - end_grad

    for p in proteins:
        if p.amount != 0.0:
            salt = _get_salt(p)

            if salt > start_grad:
                # Salt not high enough to stick
                p.k1 = IX_FLOW_THROUGH
                p.k2 = 5.0
            elif grad == 0.0:
                # Flat gradient -> stuck
                p.k1 = 1000.0
                p.k2 = 5.0
            else:
                p.k1 = IX_GRADIENT_START + (factor * (start_grad - salt) / grad)
                p.k2 = 2.0 * math.sqrt(p.amount) / grad

            p.k3 = 10.0 * p.amount / p.k2
        else:
            p.k3 = 0.0

    return set_plot_array(proteins)


def check_hic_precipitation(proteins: list[Protein], start_grad: float) -> float:
    """Check for protein precipitation at starting salt concentration. Spec 4.8."""
    total_insoluble = 0.0
    total_amount = 0.0

    for p in proteins:
        total_amount += p.amount

        log_szero = _get_log_szero(p)
        if log_szero < 1.0:
            log_szero = 1.0

        # Fiddle factor for HIC precipitation check
        beta = log_szero / HIC_BETA_DIVISOR
        molarity = start_grad
        solubility = 10.0 ** (log_szero - beta * molarity)

        precipitated = REFERENCE_CONCENTRATION - solubility
        if precipitated < 0.0:
            precipitated = 0.0

        insol = precipitated / REFERENCE_CONCENTRATION * p.amount
        if insol > p.amount:
            insol = p.amount
        if insol < 0.0:
            insol = 0.0

        total_insoluble += insol

    if total_amount > 0.0:
        return total_insoluble / total_amount
    return 0.0


def affinity(proteins: list[Protein], enzyme_index: int,
             ligand: AffinityLigand, elution: ElutionMethod) -> list[list[float]]:
    """Affinity chromatography. Spec 4.9."""
    # Scramble affinities based on enzyme_index (1-based in C++)
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    POLYCLONAL = 4
    INHIBITOR = 5
    NICKEL = 6

    affinity_ligand = 0
    i = (enzyme_index + 1) % 6

    # Determine ligand affinity level
    if ligand == AffinityLigand.ANTIBODY_A:
        affinity_ligand = [0, MEDIUM, LOW, LOW, HIGH, MEDIUM][i]
    elif ligand == AffinityLigand.ANTIBODY_B:
        affinity_ligand = [0, LOW, MEDIUM, HIGH, LOW, HIGH][i]
    elif ligand == AffinityLigand.ANTIBODY_C:
        affinity_ligand = [0, HIGH, HIGH, MEDIUM, MEDIUM, LOW][i]
    elif ligand == AffinityLigand.POLYCLONAL:
        affinity_ligand = POLYCLONAL
    elif ligand == AffinityLigand.IMMOBILIZED_INHIBITOR:
        affinity_ligand = INHIBITOR
    elif ligand == AffinityLigand.NI_NTA_AGAROSE:
        affinity_ligand = NICKEL

    for idx, p in enumerate(proteins):
        if p.amount != 0.0:
            if idx == enzyme_index:
                # This is the target enzyme
                # Check ideal situations
                ideal = (
                    (affinity_ligand == MEDIUM and elution == ElutionMethod.TRIS_BUFFER) or
                    (affinity_ligand == MEDIUM and elution == ElutionMethod.ACID_GLYCINE) or
                    (affinity_ligand == POLYCLONAL and elution == ElutionMethod.TRIS_BUFFER) or
                    (affinity_ligand == POLYCLONAL and elution == ElutionMethod.ACID_GLYCINE) or
                    (affinity_ligand == INHIBITOR and elution == ElutionMethod.INHIBITOR) or
                    (affinity_ligand == NICKEL and elution == ElutionMethod.IMIDAZOLE and p.his_tag)
                )

                if ideal:
                    p.k1 = AFFINITY_ELUTION_K1
                    gd_factor = p.k1 / 100.0

                    # Losses due to failure to elute
                    if affinity_ligand == MEDIUM:
                        p.amount *= 0.75
                    if affinity_ligand == POLYCLONAL:
                        p.amount *= 0.3
                    if affinity_ligand == INHIBITOR:
                        p.amount *= 0.8

                    # Losses due to denaturation
                    if elution == ElutionMethod.ACID_GLYCINE:
                        p.activity = p.activity // 2

                    p.k2 = gd_factor * math.sqrt(p.amount)
                    if p.k2 < MIN_PEAK_WIDTH:
                        p.k2 = MIN_PEAK_WIDTH

                elif affinity_ligand == HIGH:
                    # Infinity chromatography
                    p.k1 = AFFINITY_STUCK_K1
                    p.k2 = 5.0

                else:
                    # Default: runs straight through
                    p.k1 = 50.0
                    p.k2 = 5.0
                    # Losses due to denaturation
                    if elution == ElutionMethod.ACID_GLYCINE:
                        p.activity = p.activity // 2
            else:
                # Non-enzyme protein: always flow-through
                p.k1 = 50.0
                p.k2 = 5.0

            p.k3 = 10.0 * p.amount / p.k2
        else:
            p.k3 = 0.0

    return set_plot_array(proteins)


def pool_fractions(proteins: list[Protein], fractions: list[list[float]],
                   start: int, end: int) -> None:
    """Pool selected fractions, updating protein amounts. Spec 4.10."""
    total_amount = 0.0

    for idx, p in enumerate(proteins):
        protein_idx = idx + 1  # fractions use 1-based protein indexing
        totalarea = math.sqrt(2.0 * math.pi) * p.k2 * p.k3

        if totalarea == 0.0:
            p.amount = 0.0
        else:
            thisarea = 0.0
            if start == DISPLAY_FRACTIONS:  # 125
                thisarea = fractions[249][protein_idx] + fractions[250][protein_idx]
            elif start == end:
                thisarea = fractions[2 * start - 1][protein_idx] + fractions[2 * start][protein_idx]
            else:
                for k in range(start, end + 1):
                    thisarea += fractions[2 * k - 1][protein_idx] + fractions[2 * k][protein_idx]

            p.amount *= thisarea / totalarea
            total_amount += p.amount
