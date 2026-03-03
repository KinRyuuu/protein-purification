"""Enumerated types for the protein purification simulation."""
from enum import Enum


class SeparationType(str, Enum):
    """Available separation techniques."""
    AMMONIUM_SULFATE = "ammonium_sulfate"
    HEAT_TREATMENT = "heat_treatment"
    GEL_FILTRATION = "gel_filtration"
    ION_EXCHANGE = "ion_exchange"
    HIC = "hic"
    AFFINITY = "affinity"


class GelMatrix(str, Enum):
    """Gel filtration matrix options with different MW exclusion limits."""
    SEPHADEX_G50 = "sephadex_g50"
    SEPHADEX_G100 = "sephadex_g100"
    SEPHACRYL_S200HR = "sephacryl_s200hr"
    ULTROGEL_ACA54 = "ultrogel_aca54"
    ULTROGEL_ACA44 = "ultrogel_aca44"
    ULTROGEL_ACA34 = "ultrogel_aca34"
    BIOGEL_P60 = "biogel_p60"
    BIOGEL_P150 = "biogel_p150"
    BIOGEL_P300 = "biogel_p300"


class IonExchangeMedia(str, Enum):
    """Ion exchange resin types."""
    DEAE_CELLULOSE = "deae_cellulose"
    CM_CELLULOSE = "cm_cellulose"
    Q_SEPHAROSE = "q_sepharose"
    S_SEPHAROSE = "s_sepharose"


class GradientType(str, Enum):
    """Elution gradient types for ion exchange chromatography."""
    SALT = "salt"
    PH = "ph"


class HICMedia(str, Enum):
    """Hydrophobic interaction chromatography media."""
    PHENYL_SEPHAROSE = "phenyl_sepharose"
    OCTYL_SEPHAROSE = "octyl_sepharose"


class AffinityLigand(str, Enum):
    """Affinity chromatography ligand options."""
    ANTIBODY_A = "antibody_a"
    ANTIBODY_B = "antibody_b"
    ANTIBODY_C = "antibody_c"
    POLYCLONAL = "polyclonal"
    IMMOBILIZED_INHIBITOR = "immobilized_inhibitor"
    NI_NTA_AGAROSE = "ni_nta_agarose"


class ElutionMethod(str, Enum):
    """Affinity column elution methods."""
    TRIS_BUFFER = "tris_buffer"
    ACID_GLYCINE = "acid_glycine"
    INHIBITOR = "inhibitor"
    IMIDAZOLE = "imidazole"


class StainMode(str, Enum):
    """PAGE gel staining modes."""
    COOMASSIE = "coomassie"
    IMMUNOBLOT = "immunoblot"


class SessionPhase(str, Enum):
    """Session state machine phases."""
    SPLASH = "splash"
    MIXTURE_SELECTION = "mixture_selection"
    ENZYME_SELECTION = "enzyme_selection"
    RUNNING = "running"
    FINISHED = "finished"
