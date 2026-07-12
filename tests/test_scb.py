from scb_lvt.scb import ScbClient, ScbTable, select_table_path


class FakeScbClient(ScbClient):
    def __init__(self, tree):
        super().__init__("https://example.invalid", pause_seconds=0)
        self.tree = tree

    def get_json(self, path=""):
        return self.tree[path]


def test_select_table_path_auto_selects_unique_best_match():
    client = FakeScbClient(
        {
            "": [
                {"id": "BE", "text": "Population", "type": "l"},
                {"id": "OTHER", "text": "Other topic", "type": "l"},
            ],
            "BE": [{"id": "BE0101", "text": "Population statistics", "type": "l"}],
            "BE/BE0101": [{"id": "BefolkningNy", "text": "Population by municipality and year", "type": "t"}],
            "OTHER": [{"id": "LessGood", "text": "Population", "type": "t"}],
        }
    )
    table = ScbTable(
        name="population",
        role="demographic_control",
        description="Population by municipality/county and year.",
        search_terms=("Population", "municipality", "year"),
    )

    selected_path, candidates = select_table_path(client, table)

    assert selected_path == "BE/BE0101/BefolkningNy"
    assert candidates[0].score == 3


def test_select_table_path_keeps_ambiguous_matches_unselected():
    client = FakeScbClient(
        {
            "": [
                {"id": "A", "text": "Income", "type": "t"},
                {"id": "B", "text": "Income", "type": "t"},
            ]
        }
    )
    table = ScbTable(
        name="income",
        role="income_control",
        description="Income by municipality/county and year.",
        search_terms=("income",),
    )

    selected_path, candidates = select_table_path(client, table)

    assert selected_path is None
    assert [candidate.path for candidate in candidates] == ["A", "B"]


def test_get_json_retries_connection_reset(monkeypatch):
    import scb_lvt.scb as scb

    attempts = []

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b'{"ok": true}'

    def fake_urlopen(req, timeout):
        attempts.append((req.full_url, timeout))
        if len(attempts) == 1:
            raise ConnectionResetError("forcibly closed by remote host")
        return FakeResponse()

    monkeypatch.setattr(scb, "urlopen", fake_urlopen)
    monkeypatch.setattr(scb.time, "sleep", lambda seconds: None)

    client = ScbClient("https://example.invalid", pause_seconds=0, max_retries=1, backoff_seconds=0)

    assert client.get_json("path") == {"ok": True}
    assert len(attempts) == 2


def test_get_json_reports_exhausted_connection_reset(monkeypatch):
    import pytest
    import scb_lvt.scb as scb

    monkeypatch.setattr(scb, "urlopen", lambda req, timeout: (_ for _ in ()).throw(ConnectionResetError("reset")))
    monkeypatch.setattr(scb.time, "sleep", lambda seconds: None)

    client = ScbClient("https://example.invalid", pause_seconds=0, max_retries=1, backoff_seconds=0)

    with pytest.raises(RuntimeError, match="after 2 attempts"):
        client.get_json("path")
