"""Tests for mixture file parsing and writing.

Validates reading of bundled mixture files and
round-trip save/load of .ppmixture format. Spec §3.
"""
from pathlib import Path

from backend.engine.mixture_io import (
    list_bundled_mixtures,
    load_mixture,
    parse_json_mixture_file,
    parse_mixture_file,
    parse_ppmixture_file,
    resolve_mixture_path,
    write_json_mixture_file,
    write_ppmixture_file,
)
from backend.engine.step_record import StepRecord
from backend.engine.protein import Protein


def test_parse_default_mixture(default_mixture_path):
    """Default mixture parses to 20 proteins."""
    proteins = parse_mixture_file(default_mixture_path)
    assert len(proteins) == 20


def test_parse_easy3_mixture(easy3_mixture_path):
    """Easy3 mixture parses to 3 proteins."""
    proteins = parse_mixture_file(easy3_mixture_path)
    assert len(proteins) == 3


def test_parse_skips_comments(tmp_path):
    """Lines starting with // are ignored."""
    content = "// comment\n1\n// another comment\n10,10,0,10,0,0,0,200000,1,0,0,200000,0,0,10,10,40,2.5,11.5,155,2,2\n"
    f = tmp_path / "test.txt"
    f.write_text(content)
    proteins = parse_mixture_file(f)
    assert len(proteins) == 1
    assert proteins[0].mol_wt == 200000.0


def test_parse_protein_fields(default_mixture_path):
    """Each protein has all 22 fields populated."""
    proteins = parse_mixture_file(default_mixture_path)
    # Check first protein: 16,23,6,31,10,18,3,53500,1,0,0,53500,0,0,10,10,40,2.5,9.5,126,4,4
    p = proteins[0]
    assert p.charges == [16, 23, 6, 31, 10, 18, 3]
    assert p.mol_wt == 53500.0
    assert p.no_of_sub1 == 1
    assert p.no_of_sub2 == 0
    assert p.no_of_sub3 == 0
    assert p.subunit1 == 53500.0
    assert p.subunit2 == 0.0
    assert p.subunit3 == 0.0
    assert p.original_amount == 10.0
    assert p.amount == 10.0
    assert p.temp == 40.0
    assert p.ph1 == 2.5
    assert p.ph2 == 9.5
    assert p.hydrophobicity == 126.0
    assert p.original_activity == 4
    assert p.activity == 4
    assert p.his_tag is False


def test_parse_his_tag(default_mixture_path):
    """Protein 2 in Default_Mixture has a His-tag (field 3 = -8)."""
    proteins = parse_mixture_file(default_mixture_path)
    p2 = proteins[1]
    assert p2.his_tag is True
    assert p2.charges[2] == 8  # abs(-8)


def test_parse_complex_mixture_no_comments(data_dir):
    """Complex_Mixture.txt has no comment header."""
    proteins = parse_mixture_file(data_dir / "Complex_Mixture.txt")
    assert len(proteins) == 60


def test_parse_multi_subunit(data_dir):
    """Complex_Mixture protein 29 has 3 subunit types."""
    proteins = parse_mixture_file(data_dir / "Complex_Mixture.txt")
    p = proteins[28]  # 0-indexed line 30
    assert p.no_of_sub1 == 3
    assert p.no_of_sub2 == 5
    assert p.no_of_sub3 == 4
    assert p.subunit1 == 50000.0
    assert p.subunit2 == 20000.0
    assert p.subunit3 == 10000.0


def test_parse_non_integer_amounts(data_dir):
    """Complex_Mixture has non-integer amounts (e.g. 12.5, 5.5)."""
    proteins = parse_mixture_file(data_dir / "Complex_Mixture.txt")
    # Protein at index 40 (data line 41 in file): original_amount=12.5
    p = proteins[40]
    assert p.original_amount == 12.5
    assert p.amount == 12.5


def test_load_mixture_txt(default_mixture_path):
    """load_mixture dispatches .txt files correctly."""
    proteins = load_mixture(default_mixture_path)
    assert len(proteins) == 20


def test_load_mixture_json(data_dir):
    """load_mixture dispatches .json files correctly."""
    json_path = data_dir / "Default_Mixture.json"
    if json_path.exists():
        proteins = load_mixture(json_path)
        assert len(proteins) == 20


def test_write_and_read_json(tmp_path, default_mixture_path):
    """Write proteins to JSON and read back."""
    proteins = parse_mixture_file(default_mixture_path)
    json_path = tmp_path / "test.json"
    write_json_mixture_file(json_path, proteins)
    loaded = parse_json_mixture_file(json_path)
    assert len(loaded) == len(proteins)
    for orig, back in zip(proteins, loaded):
        assert orig.charges == back.charges
        assert orig.mol_wt == back.mol_wt
        assert orig.his_tag == back.his_tag


def test_resolve_mixture_path_prefers_json(tmp_path):
    """resolve_mixture_path prefers .json over .txt."""
    (tmp_path / "Test.txt").write_text("1\n10,10,0,10,0,0,0,200000,1,0,0,200000,0,0,10,10,40,2.5,11.5,155,2,2\n")
    (tmp_path / "Test.json").write_text('{"format_version":1,"proteins":[]}')
    path = resolve_mixture_path(tmp_path, "Test")
    assert path.suffix == ".json"


def test_resolve_mixture_path_falls_back_to_txt(tmp_path):
    """resolve_mixture_path falls back to .txt when no .json exists."""
    (tmp_path / "Test.txt").write_text("1\n10,10,0,10,0,0,0,200000,1,0,0,200000,0,0,10,10,40,2.5,11.5,155,2,2\n")
    path = resolve_mixture_path(tmp_path, "Test")
    assert path.suffix == ".txt"


def test_write_ppmixture_roundtrip(tmp_path):
    """Writing and reading a .ppmixture preserves data."""
    proteins = [
        Protein(
            charges=[16, 23, 6, 31, 10, 18, 3],
            mol_wt=53500.0, no_of_sub1=1, no_of_sub2=0, no_of_sub3=0,
            subunit1=53500.0, subunit2=0.0, subunit3=0.0,
            original_amount=10.0, amount=8.0,
            temp=40.0, ph1=2.5, ph2=9.5, hydrophobicity=126.0,
            original_activity=4, activity=4,
        ),
        Protein(
            charges=[10, 15, 8, 20, 5, 10, 2],
            mol_wt=30000.0, no_of_sub1=2, no_of_sub2=0, no_of_sub3=0,
            subunit1=15000.0, subunit2=0.0, subunit3=0.0,
            original_amount=5.0, amount=3.0,
            temp=50.0, ph1=3.0, ph2=10.0, hydrophobicity=100.0,
            original_activity=2, activity=2, his_tag=True,
        ),
    ]
    history = [
        StepRecord(step_type="Initial", protein_amount=15.0,
                   enzyme_units=2000.0, enzyme_yield=100.0,
                   enrichment=1.0, cost_per_unit=0.0),
    ]
    path = tmp_path / "test.ppmixture"
    write_ppmixture_file(path, proteins, enzyme_index=1, history=history)

    loaded_proteins, enzyme_idx, loaded_history = parse_ppmixture_file(path)
    assert len(loaded_proteins) == 2
    assert enzyme_idx == 1
    assert len(loaded_history) == 1
    assert loaded_proteins[0].mol_wt == 53500.0
    assert loaded_proteins[1].his_tag is True
    assert loaded_proteins[1].charges[2] == 8
    assert loaded_history[0].enzyme_yield == 100.0


def test_list_bundled_mixtures(data_dir):
    """Lists all mixture files in data directory."""
    names = list_bundled_mixtures(data_dir)
    assert "Default_Mixture" in names
    assert "Easy3_Mixture" in names
    assert "Complex_Mixture" in names
    assert "Example_Mixture" in names
    # Deduplicated — no duplicates from .txt and .json
    assert len(names) == len(set(names))
