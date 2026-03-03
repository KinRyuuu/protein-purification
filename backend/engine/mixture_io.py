
"""Parse and write mixture data files. Spec Section 3."""
from pathlib import Path

from .protein import Protein
from .step_record import StepRecord


def parse_mixture_file(path: Path) -> list[Protein]:
    """Parse a mixture .txt file into a list of Proteins. Spec 3.2."""
    lines: list[str] = []
    with open(path) as f:
        for raw in f:
            stripped = raw.strip()
            if stripped and not stripped.startswith("//"):
                lines.append(stripped)

    num_proteins = int(lines[0])
    proteins: list[Protein] = []
    for i in range(1, num_proteins + 1):
        fields = lines[i].split(",")
        charges_raw = [int(fields[j]) for j in range(7)]

        his_tag = charges_raw[2] < -5
        if his_tag:
            charges_raw[2] = abs(charges_raw[2])

        proteins.append(Protein(
            charges=charges_raw,
            mol_wt=float(fields[7]),
            no_of_sub1=int(fields[8]),
            no_of_sub2=int(fields[9]),
            no_of_sub3=int(fields[10]),
            subunit1=float(fields[11]),
            subunit2=float(fields[12]),
            subunit3=float(fields[13]),
            original_amount=float(fields[14]),
            amount=float(fields[15]),
            temp=float(fields[16]),
            ph1=float(fields[17]),
            ph2=float(fields[18]),
            hydrophobicity=float(fields[19]),
            original_activity=int(fields[20]),
            activity=int(fields[21]),
            his_tag=his_tag,
        ))
    return proteins


def parse_json_mixture_file(path: Path) -> list[Protein]:
    """Parse a mixture .json file into a list of Proteins."""
    from .mixture_json import json_to_proteins
    return json_to_proteins(path.read_text())


def write_json_mixture_file(path: Path, proteins: list[Protein]) -> None:
    """Write a list of Proteins to a .json mixture file."""
    from .mixture_json import proteins_to_json
    path.write_text(proteins_to_json(proteins))


def load_mixture(path: Path) -> list[Protein]:
    """Load a mixture file, dispatching by extension (.txt or .json)."""
    if path.suffix == ".json":
        return parse_json_mixture_file(path)
    return parse_mixture_file(path)


def resolve_mixture_path(data_dir: Path, name: str) -> Path:
    """Resolve a mixture display name to a file path, preferring .json."""
    json_path = data_dir / f"{name}.json"
    if json_path.exists():
        return json_path
    txt_path = data_dir / f"{name}.txt"
    if txt_path.exists():
        return txt_path
    raise FileNotFoundError(f"No mixture file found for '{name}' in {data_dir}")


def parse_ppmixture_file(path: Path) -> tuple[list[Protein], int | None, list[StepRecord]]:
    """Parse a .ppmixture file. Returns (proteins, enzyme_index, history). Spec 3.4."""
    lines: list[str] = []
    with open(path) as f:
        for raw in f:
            stripped = raw.strip()
            if stripped and not stripped.startswith("//"):
                lines.append(stripped)

    num_proteins = int(lines[0])
    proteins: list[Protein] = []
    for i in range(1, num_proteins + 1):
        fields = lines[i].split(",")
        charges_raw = [int(fields[j]) for j in range(7)]

        his_tag = charges_raw[2] < -5
        if his_tag:
            charges_raw[2] = abs(charges_raw[2])

        proteins.append(Protein(
            charges=charges_raw,
            mol_wt=float(fields[7]),
            no_of_sub1=int(fields[8]),
            no_of_sub2=int(fields[9]),
            no_of_sub3=int(fields[10]),
            subunit1=float(fields[11]),
            subunit2=float(fields[12]),
            subunit3=float(fields[13]),
            original_amount=float(fields[14]),
            amount=float(fields[15]),
            temp=float(fields[16]),
            ph1=float(fields[17]),
            ph2=float(fields[18]),
            hydrophobicity=float(fields[19]),
            original_activity=int(fields[20]),
            activity=int(fields[21]),
            his_tag=his_tag,
        ))

    # Check for history data after protein lines
    enzyme_index: int | None = None
    history: list[StepRecord] = []
    next_line = num_proteins + 1
    if next_line < len(lines):
        enzyme_index = int(lines[next_line])
        next_line += 1
        num_steps = int(lines[next_line])
        next_line += 1
        for j in range(num_steps):
            fields = lines[next_line].split(",")
            history.append(StepRecord(
                step_type=fields[0],
                protein_amount=float(fields[1]),
                enzyme_units=float(fields[2]),
                enzyme_yield=float(fields[3]),
                enrichment=float(fields[4]),
                cost_per_unit=float(fields[5]),
            ))
            next_line += 1

    return proteins, enzyme_index, history


def write_ppmixture_file(path: Path, proteins: list[Protein],
                         enzyme_index: int | None = None,
                         history: list[StepRecord] | None = None) -> None:
    """Write a .ppmixture save file. Spec 3.4."""
    lines: list[str] = []
    lines.append(str(len(proteins)))
    for p in proteins:
        charges = list(p.charges)
        if p.his_tag:
            charges[2] = -charges[2]
        fields = [
            str(charges[0]), str(charges[1]), str(charges[2]),
            str(charges[3]), str(charges[4]), str(charges[5]), str(charges[6]),
            str(p.mol_wt), str(p.no_of_sub1), str(p.no_of_sub2), str(p.no_of_sub3),
            str(p.subunit1), str(p.subunit2), str(p.subunit3),
            str(p.original_amount), str(p.amount),
            str(p.temp), str(p.ph1), str(p.ph2), str(p.hydrophobicity),
            str(p.original_activity), str(p.activity),
        ]
        lines.append(",".join(fields))

    if enzyme_index is not None:
        lines.append(str(enzyme_index))
        steps = history or []
        lines.append(str(len(steps)))
        for rec in steps:
            fields = [
                str(rec.step_type), str(rec.protein_amount),
                str(rec.enzyme_units), str(rec.enzyme_yield),
                str(rec.enrichment), str(rec.cost_per_unit),
            ]
            lines.append(",".join(fields))

    path.write_text("\n".join(lines) + "\n")


def list_bundled_mixtures(data_dir: Path) -> list[str]:
    """List available bundled mixture names, deduplicating .txt and .json."""
    stems: set[str] = set()
    for ext in ("*.txt", "*.json"):
        for p in data_dir.glob(ext):
            stems.add(p.stem)
    return sorted(stems)
