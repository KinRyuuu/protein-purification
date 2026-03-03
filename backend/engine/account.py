"""Cost tracking and purification record management. Spec Section 5."""
from .step_record import StepRecord
from .protein import Protein
from .constants import MIN_ENZYME_UNITS, MAX_STEPS, MAX_COST_PER_UNIT


class Account:
    """Tracks cumulative cost and purification step records."""

    def __init__(self) -> None:
        self.total_cost: float = 0.0
        self.records: list[StepRecord] = []
        self._initial_enzyme_units: float = 0.0
        self._initial_ratio: float = 0.0

    def get_initial_record(self, proteins: list[Protein], enzyme_index: int) -> StepRecord:
        """Create the initial (step 0) record. Spec 5.1."""
        protein_amount = sum(p.amount for p in proteins)
        enzyme = proteins[enzyme_index]
        enzyme_units = enzyme.amount * enzyme.activity * 100.0

        self._initial_enzyme_units = enzyme_units
        if protein_amount > 0.0:
            self._initial_ratio = enzyme.amount / protein_amount
        else:
            self._initial_ratio = 0.0

        record = StepRecord(
            step_type="Initial",
            protein_amount=protein_amount,
            enzyme_units=enzyme_units,
            enzyme_yield=100.0,
            enrichment=1.0,
            cost_per_unit=0.0,
        )
        self.records.append(record)
        return record

    def add_step(self, step_type: str, proteins: list[Protein],
                 enzyme_index: int, cost: float) -> StepRecord:
        """Record a purification step. Spec 5.1."""
        self.total_cost += cost

        enzyme = proteins[enzyme_index]
        protein_amount = sum(p.amount for p in proteins)
        activity_factor = enzyme.activity / enzyme.original_activity if enzyme.original_activity > 0 else 0.0
        enzyme_units = enzyme.amount * enzyme.original_activity * 100.0

        if enzyme.amount == 0.0:
            enzyme_yield = 0.0
        else:
            enzyme_yield = enzyme.amount / enzyme.original_amount * 100.0 * activity_factor

        if enzyme_yield < 0.01:
            enrichment = 0.0
        else:
            if protein_amount > 0.0 and self._initial_ratio > 0.0:
                current_ratio = enzyme.amount / protein_amount
                enrichment = (current_ratio / self._initial_ratio) * activity_factor
            else:
                enrichment = 0.0

        if enzyme_units > 0.01:
            cost_per_unit = self.total_cost * 100.0 / enzyme_units
        else:
            cost_per_unit = 0.0

        record = StepRecord(
            step_type=step_type,
            protein_amount=protein_amount,
            enzyme_units=enzyme_units,
            enzyme_yield=enzyme_yield,
            enrichment=enrichment,
            cost_per_unit=cost_per_unit,
        )
        self.records.append(record)
        return record

    def check_failure(self, proteins: list[Protein], enzyme_index: int) -> str | None:
        """Check failure conditions. Returns message or None. Spec 1.2."""
        enzyme = proteins[enzyme_index]
        enzyme_units = enzyme.amount * enzyme.activity * 100.0

        if enzyme_units < MIN_ENZYME_UNITS:
            return "You have lost the enzyme!"
        if len(self.records) == MAX_STEPS:
            return "Not finished in time"
        if self.records and self.records[-1].cost_per_unit > MAX_COST_PER_UNIT:
            return "Cost is too high!"
        return None

    def check_success(self) -> bool:
        """Return True if purification is complete (≥10-fold enrichment, ≥5% yield)."""
        if len(self.records) < 2:
            return False
        latest = self.records[-1]
        return latest.enrichment >= 10.0 and latest.enzyme_yield >= 5.0
