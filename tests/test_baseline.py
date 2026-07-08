import csv
from pathlib import Path

from scb_lvt.baseline import fit_univariate_baseline, join_measures


def write_csv(path: Path, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def test_join_and_fit(tmp_path):
    write_csv(tmp_path / "property_prices.normalized.csv", [{"region_code": "0180", "year": "2023", "property_prices": "10"}])
    write_csv(tmp_path / "income.normalized.csv", [{"region_code": "0180", "year": "2023", "income": "5"}])
    model_csv = tmp_path / "model.csv"
    join_measures(tmp_path, model_csv)

    text_out = tmp_path / "model.txt"
    fit_univariate_baseline(model_csv, "property_prices", text_out)

    assert "target=property_prices" in text_out.read_text(encoding="utf-8")
