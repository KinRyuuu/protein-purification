"""Step record dataclass for purification history. Spec Section 5.1."""
from dataclasses import dataclass


@dataclass
class StepRecord:
    """Record of a single purification step."""
    step_type: str
    protein_amount: float
    enzyme_units: float
    enzyme_yield: float
    enrichment: float
    cost_per_unit: float
