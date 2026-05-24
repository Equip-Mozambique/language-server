"""Contract tests for POST /api/uploads and GET /api/uploads/{iso}."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(corpus_root):
    from aiserver.api.app import app

    return TestClient(app)


def test_post_upload_round_trips(client):
    r = client.post(
        "/api/uploads",
        data={
            "iso": "sna",
            "speaker_id": "s1",
            "dialect": "Karanga",
            "register": "read",
            "license": "CC-BY",
            "transcript": "Mhoroi",
        },
        files={"audio": ("clip.wav", b"AUDIODATA", "audio/wav")},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["iso"] == "sna"
    assert body["uuid"]
    assert body["sha256"]


def test_list_uploads_returns_inserted(client):
    client.post(
        "/api/uploads",
        data={"iso": "sna", "register": "read", "license": "CC-BY"},
        files={"audio": ("x.wav", b"XX", "audio/wav")},
    )
    r = client.get("/api/uploads/sna")
    assert r.status_code == 200
    rows = r.json()
    assert isinstance(rows, list)
    assert len(rows) >= 1
    assert all(row["iso"] == "sna" for row in rows)


def test_list_uploads_empty_for_unseen_iso(client):
    r = client.get("/api/uploads/nya")
    assert r.status_code == 200
    assert r.json() == []


def test_upload_unknown_iso_rejected(client):
    r = client.post(
        "/api/uploads",
        data={"iso": "zzz"},
        files={"audio": ("x.wav", b"YY", "audio/wav")},
    )
    assert r.status_code in {400, 404, 422}


def test_upload_invalid_register_rejected(client):
    r = client.post(
        "/api/uploads",
        data={"iso": "sna", "register": "spaceships"},
        files={"audio": ("x.wav", b"YY", "audio/wav")},
    )
    assert r.status_code in {400, 422}


def test_upload_missing_audio_rejected(client):
    r = client.post("/api/uploads", data={"iso": "sna"})
    assert r.status_code == 422
