"""Small stdlib-only client for SCB PxWeb open data."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
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


@dataclass(frozen=True)
class ScbTableCandidate:
    """A table discovered in the SCB PxWeb navigation tree."""

    path: str
    text: str
    score: int
    matched_terms: tuple[str, ...]


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

    def table_candidates(self, search_terms: Iterable[str], max_results: int = 5) -> list[ScbTableCandidate]:
        """Return ranked SCB table paths whose tree text matches configured terms."""
        terms = tuple(term.casefold() for term in search_terms if term.strip())
        candidates: list[ScbTableCandidate] = []
        stack: list[tuple[str, str]] = [("", "")]
        while stack:
            path, breadcrumb = stack.pop()
            nodes = self.get_json(path)
            if not isinstance(nodes, list):
                continue
            for node in nodes:
                node_id = str(node.get("id", "")).strip("/")
                if not node_id:
                    continue
                node_text = str(node.get("text") or node.get("label") or node_id)
                node_path = f"{path}/{node_id}".strip("/")
                node_breadcrumb = f"{breadcrumb} / {node_text}" if breadcrumb else node_text
                node_type = str(node.get("type", "")).casefold()
                if node_type == "t":
                    score, matched_terms = _score_candidate(node_path, node_breadcrumb, terms)
                    if score:
                        candidates.append(ScbTableCandidate(node_path, node_breadcrumb, score, matched_terms))
                else:
                    stack.append((node_path, node_breadcrumb))
        return sorted(candidates, key=lambda candidate: (-candidate.score, candidate.path))[:max_results]


def _score_candidate(path: str, breadcrumb: str, terms: tuple[str, ...]) -> tuple[int, tuple[str, ...]]:
    haystack = f"{path} {breadcrumb}".casefold()
    matched = tuple(term for term in terms if term in haystack)
    if not matched:
        return 0, ()
    return len(matched), matched


def select_table_path(client: ScbClient, table: ScbTable) -> tuple[str | None, list[ScbTableCandidate]]:
    """Resolve a configured path or auto-select the highest-confidence tree match."""
    if table.path:
        return table.path, []
    candidates = client.table_candidates(table.search_terms)
    if candidates and (len(candidates) == 1 or candidates[0].score > candidates[1].score):
        return candidates[0].path, candidates
    return None, candidates


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
