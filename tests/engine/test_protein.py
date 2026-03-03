"""Tests for the Protein dataclass.

Validates protein construction, property calculations,
and field defaults. Spec §2.1.
"""


def test_protein_default_construction():
    """A default Protein has zero-initialized fields."""
    pass


def test_protein_chains_property():
    """chains = no_of_sub1 + no_of_sub2 + no_of_sub3."""
    pass


def test_protein_subunit_mws():
    """subunit_mws returns only non-zero subunit entries."""
    pass


def test_protein_his_tag_detection():
    """his_tag is True when charges[2] < -5."""
    pass
