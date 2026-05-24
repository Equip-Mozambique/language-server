"""Contract tests for GET /api/languages and /api/languages/{iso}."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from aiserver.api.app import app

    return TestClient(app)


def test_list_languages_returns_full_registry(client):
    r = client.get("/api/languages")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    from aiserver.languages import LANGS

    assert len(data) == len(LANGS)
    assert len(data) >= 18  # all target Zim/Moz languages

    isos = {lang["iso"] for lang in data}
    assert {"sna", "nya", "por", "seh", "ndc", "kck"}.issubset(isos)


def test_each_language_has_required_fields(client):
    r = client.get("/api/languages")
    data = r.json()
    for lang in data:
        assert set(lang.keys()) >= {
            "iso",
            "name",
            "country",
            "preferred_stt",
            "preferred_tts",
            "mms_iso",
            "mms_tts",
            "whisper_code",
            "proxy_iso",
            "effective_iso",
            "status",
        }
        assert lang["status"] in {"native", "proxy", "missing"}
        assert lang["preferred_stt"] in {"whisper", "mms", "toucan"}
        assert lang["preferred_tts"] in {"mms", "piper", "xtts", "toucan"}


def test_get_single_language_by_iso(client):
    r = client.get("/api/languages/sna")
    assert r.status_code == 200
    data = r.json()
    assert data["iso"] == "sna"
    assert data["name"] == "Shona"
    assert data["preferred_stt"] == "whisper"
    assert data["status"] == "native"


def test_get_single_language_proxy_resolution(client):
    """Ndau has no native MMS, falls back to Shona proxy."""
    r = client.get("/api/languages/ndc")
    assert r.status_code == 200
    data = r.json()
    assert data["iso"] == "ndc"
    assert data["status"] in {"proxy", "missing"}
    if data["status"] == "proxy":
        assert data["effective_iso"] == "sna"


def test_unknown_iso_returns_404(client):
    r = client.get("/api/languages/zzz")
    assert r.status_code == 404
