"""Small stdlib-only client for SCB PxWeb open data."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class ScbTable:
    """A configured SCB table and its modelling role."""

    name: str
    role: str
    description: str
    path: str | None = None
    search_terms: tuple[str, ...] = ()


class ScbClient:
    """Thin PxWeb v1 client that needs no API key."""

    def __init__(self, api_base: str, pause_seconds: float = 0.4) -> None:
        self.api_base = api_base.rstrip("/")
        self.pause_seconds = pause_seconds

    def get_json(self, path: str = "") -> Any:
        url = f"{self.api_base}/{path.strip('/')}" if path else self.api_base
        req = Request(url, headers={"User-Agent": "lvt-in-sweden/0.1"})
        try:
            with urlopen(req, timeout=45) as response:  # nosec B310: configured public SCB URL
                return json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError) as exc:
            raise RuntimeError(f"SCB request failed for {url}: {exc}") from exc
        finally:
            time.sleep(self.pause_seconds)

    def post_json(self, path: str, payload: dict[str, Any]) -> Any:
        url = f"{self.api_base}/{path.strip('/')}"
        data = json.dumps(payload).encode("utf-8")
        req = Request(
            url,
            data=data,
            method="POST",
            headers={"Content-Type": "application/json", "User-Agent": "lvt-in-sweden/0.1"},
        )
        try:
            with urlopen(req, timeout=90) as response:  # nosec B310: configured public SCB URL
                return json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError) as exc:
            raise RuntimeError(f"SCB query failed for {url}: {exc}") from exc
        finally:
            time.sleep(self.pause_seconds)

    def metadata(self, table_path: str) -> dict[str, Any]:
        return self.get_json(table_path)

    def query_all(self, table_path: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        meta = metadata or self.metadata(table_path)
        query = {
            "query": [
                {"code": variable["code"], "selection": {"filter": "all", "values": ["*"]}}
                for variable in meta.get("variables", [])
            ],
            "response": {"format": "json-stat2"},
        }
        return self.post_json(table_path, query)


def load_manifest(path: str | Path) -> tuple[str, list[ScbTable]]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    tables = [
        ScbTable(
            name=item["name"],
            role=item["role"],
            description=item["description"],
            path=item.get("path"),
            search_terms=tuple(item.get("search_terms", ())),
        )
        for item in raw["datasets"]
    ]
    return raw["api_base"], tables


def save_json(path: str | Path, payload: Any) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
