"""JSON-stat 2 to rows for SCB responses."""
from __future__ import annotations

from itertools import product
from typing import Any


def jsonstat_to_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    ids = payload["id"]
    dimensions = payload["dimension"]
    values = payload.get("value", [])
    labels = []
    for dim_id in ids:
        category = dimensions[dim_id]["category"]
        index = category["index"]
        by_position = {pos: code for code, pos in index.items()}
        labels.append([(by_position[pos], category.get("label", {}).get(by_position[pos], by_position[pos])) for pos in range(len(index))])

    rows: list[dict[str, Any]] = []
    for flat_index, coords in enumerate(product(*labels)):
        value = values[flat_index] if flat_index < len(values) else None
        row: dict[str, Any] = {"value": value}
        for dim_id, (code, label) in zip(ids, coords):
            row[f"{dim_id}_code"] = code
            row[f"{dim_id}_label"] = label
        rows.append(row)
    return rows
