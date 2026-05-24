"""Contract tests for GET /api/resources/{iso}."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(corpus_root, tmp_path, monkeypatch):
    # Minimal DBS catalog fixture
    d = tmp_path / "bible_catalogs"
    d.mkdir()
    (d / "filtered_bibles.json").write_text(
        json.dumps([{"id": "SEHBSM", "iso": "seh", "tt": "Chisena Bible", "dt": "2017"}])
    )
    md = tmp_path / "RESEARCH.md"
    md.write_text(
        "## Per-Language Deep-Dive: Sena (seh)\n\nSena resource entry.\n\n## License Caveat\n"
    )
    monkeypatch.setenv("AISERVER_BIBLE_CATALOGS", str(d))
    monkeypatch.setenv("AISERVER_RESEARCH_MD", str(md))

    from aiserver.api.app import app

    return TestClient(app)


def test_get_resources_for_known_iso(client):
    r = client.get("/api/resources/seh")
    assert r.status_code == 200
    body = r.json()
    assert body["iso"] == "seh"
    assert body["model_coverage"]["mms_iso"] == "seh"
    assert len(body["dbs_bibles"]) == 1
    assert "Sena resource entry" in body["research_md"]


def test_get_resources_unknown_iso_returns_404(client):
    r = client.get("/api/resources/zzz")
    assert r.status_code == 404
