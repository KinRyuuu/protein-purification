"""Purification session state machine. Spec Section 9."""
from .protein import Protein
from .account import Account
from .enums import SessionPhase


class PurificationSession:
    """Manages the full state of a purification session.

    Tracks current proteins, fractions, separation state,
    and enforces the state machine rules from Spec 9.3-9.4.
    """

    def __init__(self, session_id: str) -> None:
        self.session_id: str = session_id
        self.phase: SessionPhase = SessionPhase.SPLASH
        self.mixture_name: str = ""
        self.proteins: list[Protein] = []
        self.enzyme_index: int = -1
        self.account: Account = Account()
        self.fractions: list[list[float]] = []
        # State flags (Spec 9.3)
        self.pooled: bool = True
        self.has_fractions: bool = False
        self.assayed: bool = False
        self.has_gradient: bool = False
        self.two_d_gel: bool = False
        self.show_blot: bool = False
        self.scale: float = 0.5
        self.over_diluted: bool = False
        self.step: int = 0
        self.created_at: float = 0.0
        # Display metadata (Spec 5.7)
        self.gradient_start: float = 0.0
        self.gradient_end: float = 0.0
        self.gradient_type: str = ""
        self.separation_title: str = ""
        # Intermediate state for two-step flows
        self.as_result: dict | None = None
        self.gel_data: list | None = None
        self.hic_precipitation: float = 0.0

    def can_separate(self) -> bool:
        """Whether separation menu should be enabled. Spec 9.4."""
        return self.pooled and self.phase == SessionPhase.RUNNING

    def can_pool(self) -> bool:
        """Whether fractions menu should be enabled. Spec 9.4."""
        return self.has_fractions and not self.pooled

    def can_assay(self) -> bool:
        """Whether assay is available. Spec 9.4."""
        return self.has_fractions and not self.assayed

    def can_dilute(self) -> bool:
        """Whether dilution is available. Spec 9.4."""
        return self.has_fractions and not self.over_diluted

    def to_state_dict(self) -> dict:
        """Serialize session state for API response."""
        state: dict = {
            "session_id": self.session_id,
            "phase": self.phase.value,
            "mixture_name": self.mixture_name,
            "enzyme_index": self.enzyme_index,
            "pooled": self.pooled,
            "has_fractions": self.has_fractions,
            "assayed": self.assayed,
            "has_gradient": self.has_gradient,
            "two_d_gel": self.two_d_gel,
            "show_blot": self.show_blot,
            "scale": self.scale,
            "over_diluted": self.over_diluted,
            "step": self.step,
            "can_separate": self.can_separate(),
            "can_pool": self.can_pool(),
            "can_assay": self.can_assay(),
            "can_dilute": self.can_dilute(),
            "gradient_start": self.gradient_start,
            "gradient_end": self.gradient_end,
            "gradient_type": self.gradient_type,
            "separation_title": self.separation_title,
            "fractions": self.fractions if self.fractions else [],
            "records": [
                {
                    "step_type": r.step_type,
                    "protein_amount": r.protein_amount,
                    "enzyme_units": r.enzyme_units,
                    "enzyme_yield": r.enzyme_yield,
                    "enrichment": r.enrichment,
                    "cost_per_unit": r.cost_per_unit,
                }
                for r in self.account.records
            ],
            "proteins": [
                {
                    "index": i,
                    "name": f"Protein {i + 1}",
                    "mol_wt": p.mol_wt,
                    "amount": p.amount,
                    "activity": p.activity,
                    "isopoint": p.isopoint,
                    "stability": {
                        "temp": p.temp,
                        "ph1": p.ph1,
                        "ph2": p.ph2,
                    },
                }
                for i, p in enumerate(self.proteins)
            ],
        }

        if self.as_result is not None:
            state["as_result"] = self.as_result

        if self.gel_data is not None:
            state["gel_data"] = self.gel_data

        if self.hic_precipitation >= 0.001:
            state["hic_precipitation"] = self.hic_precipitation

        failure = self.account.check_failure(self.proteins, self.enzyme_index) if (
            self.phase == SessionPhase.FINISHED and self.enzyme_index >= 0
        ) else None
        if failure:
            state["failure_message"] = failure

        return state
