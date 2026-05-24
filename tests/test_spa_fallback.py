"""SPA deep-link fallback: any non-API GET that isn't a static file
returns index.html so Angular's router can take over client-side."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Stand up a fake frontend dist + point app's static mount at it."""
    front = tmp_path / "browser"
    front.mkdir()
    (front / "index.html").write_text(
        "<!doctype html><html><head><title>BatePapo</title></head><body>"
        "<app-root></app-root></body></html>"
    )
    (front / "favicon.ico").write_bytes(b"\x00\x00\x01")
    (front / "main-ABC123.js").write_text("// fake bundle")

    monkeypatch.setenv("AISERVER_FRONTEND_DIR", str(front))

    # Force fresh app instantiation so the static mount picks up the env var.
    import importlib
    import aiserver.api.app as app_mod

    importlib.reload(app_mod)
    return TestClient(app_mod.app)


def test_root_returns_index(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "BatePapo" in r.text


def test_known_static_asset_served_directly(client):
    r = client.get("/favicon.ico")
    assert r.status_code == 200


def test_deep_link_resources_returns_index(client):
    r = client.get("/resources")
    assert r.status_code == 200
    assert "BatePapo" in r.text


def test_deep_link_live_returns_index(client):
    r = client.get("/live")
    assert r.status_code == 200


def test_nested_deep_link_returns_index(client):
    """Future deep-links like /resources/seh should also fall back."""
    r = client.get("/resources/seh")
    assert r.status_code == 200
    assert "BatePapo" in r.text


def test_api_404_is_not_overridden(client):
    """The fallback only catches the static-file scope — /api routes preserve their own 404s."""
    r = client.get("/api/languages/zzz")
    assert r.status_code == 404
