"""Tests for JSON serialization/deserialization of mixture data."""
from backend.engine.mixture_io import parse_mixture_file
from backend.engine.mixture_json import (
    dict_to_protein,
    json_to_proteins,
    protein_to_dict,
    proteins_to_json,
)
from backend.engine.protein import Protein


def _make_simple_protein() -> Protein:
    return Protein(
        charges=[16, 23, 6, 31, 10, 18, 3],
        mol_wt=53500.0,
        no_of_sub1=1,
        subunit1=53500.0,
        original_amount=10.0,
        amount=10.0,
        temp=40.0,
        ph1=2.5,
        ph2=9.5,
        hydrophobicity=126.0,
        original_activity=4,
        activity=4,
    )


def test_protein_to_dict_residues():
    """Residues are stored with named keys."""
    d = protein_to_dict(_make_simple_protein())
    assert d["residues"]["asp"] == 16
    assert d["residues"]["glu"] == 23
    assert d["residues"]["his"] == 6
    assert d["residues"]["cys_sh"] == 3


def test_protein_to_dict_single_subunit():
    """Single-subunit protein has one subunit entry."""
    d = protein_to_dict(_make_simple_protein())
    assert len(d["subunits"]) == 1
    assert d["subunits"][0] == {"count": 1, "molecular_weight": 53500.0}


def test_protein_to_dict_multi_subunit():
    """Multi-subunit protein has correct entries."""
    p = Protein(
        charges=[22, 25, 8, 19, 26, 12, 5],
        mol_wt=320000.0,
        no_of_sub1=4, subunit1=50000.0,
        no_of_sub2=4, subunit2=30000.0,
        original_amount=42.0, amount=42.0,
        temp=60.0, ph1=5.0, ph2=10.5,
        hydrophobicity=167.0, original_activity=2, activity=2,
    )
    d = protein_to_dict(p)
    assert len(d["subunits"]) == 2
    assert d["subunits"][0] == {"count": 4, "molecular_weight": 50000.0}
    assert d["subunits"][1] == {"count": 4, "molecular_weight": 30000.0}


def test_protein_to_dict_three_subunits():
    """3-subunit protein serializes all three."""
    p = Protein(
        charges=[41, 21, 12, 40, 18, 12, 0],
        mol_wt=290000.0,
        no_of_sub1=3, subunit1=50000.0,
        no_of_sub2=5, subunit2=20000.0,
        no_of_sub3=4, subunit3=10000.0,
        original_amount=18.0, amount=18.0,
        temp=75.0, ph1=3.5, ph2=11.0,
        hydrophobicity=60.0, original_activity=9, activity=9,
    )
    d = protein_to_dict(p)
    assert len(d["subunits"]) == 3


def test_protein_to_dict_his_tag():
    """His-tag is serialized as a boolean."""
    p = _make_simple_protein()
    p.his_tag = True
    d = protein_to_dict(p)
    assert d["his_tag"] is True


def test_protein_to_dict_stability():
    """Stability groups temp/pH fields."""
    d = protein_to_dict(_make_simple_protein())
    assert d["stability"] == {"max_temp": 40.0, "ph_min": 2.5, "ph_max": 9.5}


def test_dict_roundtrip():
    """protein_to_dict -> dict_to_protein preserves all fields."""
    orig = _make_simple_protein()
    restored = dict_to_protein(protein_to_dict(orig))
    assert restored.charges == orig.charges
    assert restored.mol_wt == orig.mol_wt
    assert restored.no_of_sub1 == orig.no_of_sub1
    assert restored.subunit1 == orig.subunit1
    assert restored.original_amount == orig.original_amount
    assert restored.amount == orig.amount
    assert restored.temp == orig.temp
    assert restored.ph1 == orig.ph1
    assert restored.ph2 == orig.ph2
    assert restored.hydrophobicity == orig.hydrophobicity
    assert restored.original_activity == orig.original_activity
    assert restored.activity == orig.activity
    assert restored.his_tag == orig.his_tag


def test_dict_roundtrip_his_tag():
    """His-tag survives dict roundtrip."""
    p = _make_simple_protein()
    p.his_tag = True
    restored = dict_to_protein(protein_to_dict(p))
    assert restored.his_tag is True


def test_dict_roundtrip_multi_subunit():
    """Multi-subunit protein survives dict roundtrip."""
    p = Protein(
        charges=[22, 25, 8, 19, 26, 12, 5],
        mol_wt=320000.0,
        no_of_sub1=4, subunit1=50000.0,
        no_of_sub2=4, subunit2=30000.0,
        original_amount=42.0, amount=42.0,
        temp=60.0, ph1=5.0, ph2=10.5,
        hydrophobicity=167.0, original_activity=2, activity=2,
    )
    restored = dict_to_protein(protein_to_dict(p))
    assert restored.no_of_sub1 == 4
    assert restored.no_of_sub2 == 4
    assert restored.subunit1 == 50000.0
    assert restored.subunit2 == 30000.0


def test_json_full_roundtrip():
    """proteins_to_json -> json_to_proteins preserves all proteins."""
    proteins = [_make_simple_protein()]
    proteins[0].his_tag = True
    text = proteins_to_json(proteins)
    restored = json_to_proteins(text)
    assert len(restored) == 1
    assert restored[0].his_tag is True
    assert restored[0].charges == proteins[0].charges


def test_file_roundtrip_default(default_mixture_path):
    """Full roundtrip: txt -> Protein -> JSON -> Protein for Default_Mixture."""
    original = parse_mixture_file(default_mixture_path)
    text = proteins_to_json(original)
    restored = json_to_proteins(text)
    assert len(restored) == len(original)
    for orig, back in zip(original, restored):
        assert orig.charges == back.charges
        assert orig.mol_wt == back.mol_wt
        assert orig.his_tag == back.his_tag
        assert orig.no_of_sub1 == back.no_of_sub1
        assert orig.no_of_sub2 == back.no_of_sub2
        assert orig.no_of_sub3 == back.no_of_sub3
        assert orig.subunit1 == back.subunit1
        assert orig.subunit2 == back.subunit2
        assert orig.subunit3 == back.subunit3
        assert orig.original_amount == back.original_amount
        assert orig.amount == back.amount
        assert orig.temp == back.temp
        assert orig.ph1 == back.ph1
        assert orig.ph2 == back.ph2
        assert orig.hydrophobicity == back.hydrophobicity
        assert orig.original_activity == back.original_activity
        assert orig.activity == back.activity


def test_file_roundtrip_complex(data_dir):
    """Full roundtrip for Complex_Mixture (60 proteins, multi-subunit)."""
    original = parse_mixture_file(data_dir / "Complex_Mixture.txt")
    text = proteins_to_json(original)
    restored = json_to_proteins(text)
    assert len(restored) == 60
    for orig, back in zip(original, restored):
        assert orig.charges == back.charges
        assert orig.mol_wt == back.mol_wt
        assert orig.no_of_sub1 == back.no_of_sub1
        assert orig.no_of_sub2 == back.no_of_sub2
        assert orig.no_of_sub3 == back.no_of_sub3


def test_file_roundtrip_all_mixtures(data_dir):
    """Roundtrip works for all 4 bundled mixtures."""
    for name in ("Default_Mixture", "Easy3_Mixture", "Complex_Mixture", "Example_Mixture"):
        original = parse_mixture_file(data_dir / f"{name}.txt")
        text = proteins_to_json(original)
        restored = json_to_proteins(text)
        assert len(restored) == len(original), f"Count mismatch for {name}"
        for i, (orig, back) in enumerate(zip(original, restored)):
            assert orig.charges == back.charges, f"{name} protein {i} charges mismatch"
            assert orig.mol_wt == back.mol_wt, f"{name} protein {i} mol_wt mismatch"
