"""CLI utility for converting mixture files between txt and JSON formats.

Usage:
    python -m scripts.convert_mixtures txt2json [--input DIR] [--output DIR]
    python -m scripts.convert_mixtures json2txt [--input DIR] [--output DIR]
    python -m scripts.convert_mixtures convert FILE [--output FILE]
"""
import argparse
import sys
from pathlib import Path

# Allow running from the protein_purification_web directory
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.engine.mixture_io import parse_mixture_file, write_json_mixture_file
from backend.engine.mixture_json import json_to_proteins, proteins_to_json

_DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "mixtures"


def _write_txt(path: Path, proteins: list) -> None:
    """Write proteins back to the legacy .txt format."""
    lines: list[str] = []
    lines.append(str(len(proteins)))
    for p in proteins:
        his_field = -abs(p.charges[2]) if p.his_tag else p.charges[2]
        fields = [
            str(p.charges[0]), str(p.charges[1]), str(his_field),
            str(p.charges[3]), str(p.charges[4]), str(p.charges[5]),
            str(p.charges[6]),
            str(p.mol_wt) if p.mol_wt != int(p.mol_wt) else str(int(p.mol_wt)),
            str(p.no_of_sub1), str(p.no_of_sub2), str(p.no_of_sub3),
            str(p.subunit1) if p.subunit1 != int(p.subunit1) else str(int(p.subunit1)),
            str(p.subunit2) if p.subunit2 != int(p.subunit2) else str(int(p.subunit2)),
            str(p.subunit3) if p.subunit3 != int(p.subunit3) else str(int(p.subunit3)),
            str(p.original_amount) if p.original_amount != int(p.original_amount) else str(int(p.original_amount)),
            str(p.amount) if p.amount != int(p.amount) else str(int(p.amount)),
            str(p.temp) if p.temp != int(p.temp) else str(int(p.temp)),
            str(p.ph1) if p.ph1 != int(p.ph1) else str(int(p.ph1)),
            str(p.ph2) if p.ph2 != int(p.ph2) else str(int(p.ph2)),
            str(p.hydrophobicity) if p.hydrophobicity != int(p.hydrophobicity) else str(int(p.hydrophobicity)),
            str(p.original_activity), str(p.activity),
        ]
        lines.append(",".join(fields))
    path.write_text("\n".join(lines) + "\n")


def cmd_txt2json(args: argparse.Namespace) -> None:
    input_dir = Path(args.input)
    output_dir = Path(args.output) if args.output else input_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    for txt_file in sorted(input_dir.glob("*.txt")):
        proteins = parse_mixture_file(txt_file)
        out_path = output_dir / (txt_file.stem + ".json")
        write_json_mixture_file(out_path, proteins)
        print(f"{txt_file.name} -> {out_path.name} ({len(proteins)} proteins)")


def cmd_json2txt(args: argparse.Namespace) -> None:
    input_dir = Path(args.input)
    output_dir = Path(args.output) if args.output else input_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    for json_file in sorted(input_dir.glob("*.json")):
        proteins = json_to_proteins(json_file.read_text())
        out_path = output_dir / (json_file.stem + ".txt")
        _write_txt(out_path, proteins)
        print(f"{json_file.name} -> {out_path.name} ({len(proteins)} proteins)")


def cmd_convert(args: argparse.Namespace) -> None:
    src = Path(args.file)
    if not src.exists():
        print(f"Error: {src} not found", file=sys.stderr)
        sys.exit(1)

    if src.suffix == ".txt":
        proteins = parse_mixture_file(src)
        default_out = src.with_suffix(".json")
        out_path = Path(args.output) if args.output else default_out
        write_json_mixture_file(out_path, proteins)
    elif src.suffix == ".json":
        proteins = json_to_proteins(src.read_text())
        default_out = src.with_suffix(".txt")
        out_path = Path(args.output) if args.output else default_out
        _write_txt(out_path, proteins)
    else:
        print(f"Error: unsupported extension {src.suffix}", file=sys.stderr)
        sys.exit(1)

    print(f"{src.name} -> {out_path.name} ({len(proteins)} proteins)")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert mixture files between txt and JSON formats."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_t2j = sub.add_parser("txt2json", help="Convert all .txt files in a directory to .json")
    p_t2j.add_argument("--input", default=str(_DEFAULT_DATA_DIR),
                        help="Input directory (default: data/mixtures)")
    p_t2j.add_argument("--output", default=None,
                        help="Output directory (default: same as input)")
    p_t2j.set_defaults(func=cmd_txt2json)

    p_j2t = sub.add_parser("json2txt", help="Convert all .json files in a directory to .txt")
    p_j2t.add_argument("--input", default=str(_DEFAULT_DATA_DIR),
                        help="Input directory (default: data/mixtures)")
    p_j2t.add_argument("--output", default=None,
                        help="Output directory (default: same as input)")
    p_j2t.set_defaults(func=cmd_json2txt)

    p_conv = sub.add_parser("convert", help="Convert a single file")
    p_conv.add_argument("file", help="File to convert (.txt or .json)")
    p_conv.add_argument("--output", default=None, help="Output file path")
    p_conv.set_defaults(func=cmd_convert)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
