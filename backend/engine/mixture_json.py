"""JSON serialization for mixture protein data."""
import json

from .protein import Protein

_RESIDUE_KEYS = ("asp", "glu", "his", "lys", "arg", "tyr", "cys_sh")

FORMAT_VERSION = 1


def protein_to_dict(p: Protein) -> dict:
    """Convert a Protein to a JSON-ready dict matching the schema."""
    residues = {key: val for key, val in zip(_RESIDUE_KEYS, p.charges)}

    subunits = []
    for count, mw in (
        (p.no_of_sub1, p.subunit1),
        (p.no_of_sub2, p.subunit2),
        (p.no_of_sub3, p.subunit3),
    ):
        if count > 0 and mw > 0:
            subunits.append({"count": count, "molecular_weight": mw})

    return {
        "residues": residues,
        "his_tag": p.his_tag,
        "molecular_weight": p.mol_wt,
        "subunits": subunits,
        "original_amount": p.original_amount,
        "amount": p.amount,
        "stability": {
            "max_temp": p.temp,
            "ph_min": p.ph1,
            "ph_max": p.ph2,
        },
        "hydrophobicity": p.hydrophobicity,
        "original_activity": p.original_activity,
        "activity": p.activity,
    }


def dict_to_protein(d: dict) -> Protein:
    """Convert a JSON dict back to a Protein."""
    res = d["residues"]
    charges = [res[key] for key in _RESIDUE_KEYS]

    sub_list = d.get("subunits", [])
    no_of_sub1 = sub_list[0]["count"] if len(sub_list) > 0 else 1
    subunit1 = sub_list[0]["molecular_weight"] if len(sub_list) > 0 else 0.0
    no_of_sub2 = sub_list[1]["count"] if len(sub_list) > 1 else 0
    subunit2 = sub_list[1]["molecular_weight"] if len(sub_list) > 1 else 0.0
    no_of_sub3 = sub_list[2]["count"] if len(sub_list) > 2 else 0
    subunit3 = sub_list[2]["molecular_weight"] if len(sub_list) > 2 else 0.0

    stab = d.get("stability", {})

    return Protein(
        charges=charges,
        mol_wt=float(d["molecular_weight"]),
        no_of_sub1=no_of_sub1,
        no_of_sub2=no_of_sub2,
        no_of_sub3=no_of_sub3,
        subunit1=float(subunit1),
        subunit2=float(subunit2),
        subunit3=float(subunit3),
        original_amount=float(d["original_amount"]),
        amount=float(d["amount"]),
        temp=float(stab.get("max_temp", 0)),
        ph1=float(stab.get("ph_min", 0)),
        ph2=float(stab.get("ph_max", 0)),
        hydrophobicity=float(d["hydrophobicity"]),
        original_activity=int(d["original_activity"]),
        activity=int(d["activity"]),
        his_tag=bool(d.get("his_tag", False)),
    )


def proteins_to_json(proteins: list[Protein]) -> str:
    """Serialize a list of Proteins to a JSON string."""
    data = {
        "format_version": FORMAT_VERSION,
        "proteins": [protein_to_dict(p) for p in proteins],
    }
    return json.dumps(data, indent=2) + "\n"


def json_to_proteins(text: str) -> list[Protein]:
    """Deserialize a JSON string to a list of Proteins."""
    data = json.loads(text)
    return [dict_to_protein(d) for d in data["proteins"]]
