from __future__ import annotations

import argparse
import csv
from pathlib import Path

from .baseline import fit_univariate_baseline, join_measures, normalize_measure_csv
from .jsonstat import jsonstat_to_rows
from .scb import ScbClient, load_manifest, save_json, select_table_path


def cmd_fetch(args: argparse.Namespace) -> None:
    api_base, tables = load_manifest(args.manifest)
    client = ScbClient(api_base)
    for table in tables:
        selected_path, candidates = select_table_path(client, table)
        if not selected_path:
            print(f"skip {table.name}: no unique SCB table path found")
            for candidate in candidates:
                print(f"  candidate score={candidate.score} path={candidate.path} text={candidate.text}")
            continue
        if not table.path:
            print(f"auto-selected {table.name}: {selected_path}")
        meta = client.metadata(selected_path)
        save_json(Path(args.raw_dir) / f"{table.name}.metadata.json", meta)
        payload = client.query_all(selected_path, meta)
        save_json(Path(args.raw_dir) / f"{table.name}.json", payload)
        rows = jsonstat_to_rows(payload)
        out = Path(args.processed_dir) / f"{table.name}.csv"
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=rows[0].keys() if rows else ["value"])
            writer.writeheader()
            writer.writerows(rows)


def cmd_build(args: argparse.Namespace) -> None:
    processed = Path(args.processed_dir)
    for csv_path in processed.glob("*.csv"):
        if csv_path.name.endswith(".normalized.csv") or csv_path.name == "scb_baseline_model.csv":
            continue
        normalize_measure_csv(csv_path, processed / f"{csv_path.stem}.normalized.csv", csv_path.stem)
    join_measures(processed, processed / "scb_baseline_model.csv")
    fit_univariate_baseline(processed / "scb_baseline_model.csv", args.target, Path(args.model_out))


def main() -> None:
    parser = argparse.ArgumentParser(description="SCB open-data LVT baseline")
    sub = parser.add_subparsers(required=True)
    fetch = sub.add_parser("fetch", help="download configured SCB tables")
    fetch.add_argument("--manifest", default="config/scb_baseline_tables.json")
    fetch.add_argument("--raw-dir", default="data/raw/scb")
    fetch.add_argument("--processed-dir", default="data/processed")
    fetch.set_defaults(func=cmd_fetch)
    build = sub.add_parser("build", help="normalize CSVs, join controls, and fit baseline")
    build.add_argument("--processed-dir", default="data/processed")
    build.add_argument("--target", default="property_prices")
    build.add_argument("--model-out", default="models/scb_baseline.txt")
    build.set_defaults(func=cmd_build)
    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
