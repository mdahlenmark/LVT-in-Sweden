"""Build a reproducible SCB-only modelling table and linear baseline."""
from __future__ import annotations

import csv
import math
from pathlib import Path


def _first_matching(row: dict[str, str], needles: tuple[str, ...]) -> str | None:
    lowered = {key.lower(): key for key in row}
    for needle in needles:
        for key_lower, key in lowered.items():
            if needle.lower() in key_lower and key_lower.endswith("code"):
                return row[key]
    return None


def normalize_measure_csv(input_csv: Path, output_csv: Path, measure_name: str) -> None:
    with input_csv.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for row in reader:
            region = _first_matching(row, ("region", "kommun", "county", "län"))
            year = _first_matching(row, ("time", "tid", "år"))
            if region and year:
                rows.append({"region_code": region, "year": year, measure_name: row.get("value", "")})
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["region_code", "year", measure_name])
        writer.writeheader()
        writer.writerows(rows)


def join_measures(processed_dir: Path, output_csv: Path) -> None:
    joined: dict[tuple[str, str], dict[str, str]] = {}
    measures: list[str] = []
    for csv_path in sorted(processed_dir.glob("*.normalized.csv")):
        with csv_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            measure = [field for field in (reader.fieldnames or []) if field not in {"region_code", "year"}][0]
            measures.append(measure)
            for row in reader:
                key = (row["region_code"], row["year"])
                joined.setdefault(key, {"region_code": key[0], "year": key[1]})[measure] = row[measure]
    fields = ["region_code", "year", *measures]
    with output_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(joined.values())


def fit_univariate_baseline(model_csv: Path, target: str, output_txt: Path) -> None:
    with model_csv.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    features = [f for f in (rows[0].keys() if rows else []) if f not in {"region_code", "year", target}]
    lines = ["SCB no-key baseline", f"target={target}", f"features={','.join(features)}"]
    for feature in features:
        pairs = []
        for row in rows:
            try:
                pairs.append((float(row[feature]), float(row[target])))
            except (TypeError, ValueError):
                continue
        if len(pairs) < 2:
            lines.append(f"{feature}: insufficient data")
            continue
        xs, ys = zip(*pairs)
        xbar, ybar = sum(xs) / len(xs), sum(ys) / len(ys)
        denom = sum((x - xbar) ** 2 for x in xs)
        slope = sum((x - xbar) * (y - ybar) for x, y in pairs) / denom if denom else math.nan
        intercept = ybar - slope * xbar if not math.isnan(slope) else math.nan
        lines.append(f"{feature}: y = {intercept:.6g} + {slope:.6g} * x; n={len(pairs)}")
    output_txt.parent.mkdir(parents=True, exist_ok=True)
    output_txt.write_text("\n".join(lines) + "\n", encoding="utf-8")
