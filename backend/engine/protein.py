"""Individual protein entity with biochemical properties."""
from dataclasses import dataclass, field


@dataclass
class Protein:
    """A protein in the purification mixture.

    Attributes correspond to spec.md Section 2.1.
    """
    charges: list[int] = field(default_factory=lambda: [0] * 7)
    mol_wt: float = 0.0
    no_of_sub1: int = 1
    no_of_sub2: int = 0
    no_of_sub3: int = 0
    subunit1: float = 0.0
    subunit2: float = 0.0
    subunit3: float = 0.0
    original_amount: float = 0.0
    amount: float = 0.0
    temp: float = 0.0
    ph1: float = 0.0
    ph2: float = 0.0
    hydrophobicity: float = 0.0
    original_activity: int = 0
    activity: int = 0
    isopoint: float = 0.0
    his_tag: bool = False
    k1: float = 0.0
    k2: float = 0.0
    k3: float = 0.0

    @property
    def chains(self) -> int:
        """Total number of polypeptide chains."""
        return self.no_of_sub1 + self.no_of_sub2 + self.no_of_sub3

    @property
    def subunit_mws(self) -> list[tuple[float, int]]:
        """List of (subunit_mw, count) for non-zero subunits."""
        result: list[tuple[float, int]] = []
        if self.subunit1 > 0:
            result.append((self.subunit1, self.no_of_sub1))
        if self.subunit2 > 0:
            result.append((self.subunit2, self.no_of_sub2))
        if self.subunit3 > 0:
            result.append((self.subunit3, self.no_of_sub3))
        return result
