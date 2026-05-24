"""Tests for upload corpus: filesystem layout + sqlite metadata."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest


def test_add_upload_writes_file_and_meta_row(corpus_root: Path):
    from aiserver.corpus import add_upload, list_uploads

    payload = b"FAKE_AUDIO_BYTES"
    meta = {
        "filename_orig": "clip.wav",
        "media_type": "audio/wav",
        "speaker_id": "spk1",
        "dialect": "Lilima",
        "register": "read",
        "license": "CC-BY",
        "transcript": "Mhoroi makadii",
    }
    rec = add_upload("sna", payload, meta)
    assert rec["uuid"]
    assert rec["sha256"] == hashlib.sha256(payload).hexdigest()
    stored = Path(rec["path"])
    assert stored.exists()
    assert stored.read_bytes() == payload
    # File lives under corpus_root/sna/raw/
    assert stored.parent.parent == corpus_root / "sna"

    rows = list_uploads("sna")
    assert len(rows) == 1
    assert rows[0]["uuid"] == rec["uuid"]
    assert rows[0]["speaker_id"] == "spk1"
    assert rows[0]["dialect"] == "Lilima"
    assert rows[0]["transcript"] == "Mhoroi makadii"
    assert rows[0]["register"] == "read"
    assert rows[0]["license"] == "CC-BY"


def test_add_upload_dedup_on_sha256(corpus_root: Path):
    from aiserver.corpus import add_upload, list_uploads

    payload = b"SAME_BYTES"
    a = add_upload("sna", payload, {"filename_orig": "a.wav"})
    b = add_upload("sna", payload, {"filename_orig": "b.wav"})
    # Same content → same uuid (dedup)
    assert a["uuid"] == b["uuid"]
    assert a["sha256"] == b["sha256"]
    assert len(list_uploads("sna")) == 1


def test_add_upload_separate_iso_separate_db(corpus_root: Path):
    from aiserver.corpus import add_upload, list_uploads

    add_upload("sna", b"AAA", {"filename_orig": "a.wav"})
    add_upload("seh", b"BBB", {"filename_orig": "b.wav"})
    assert len(list_uploads("sna")) == 1
    assert len(list_uploads("seh")) == 1
    assert len(list_uploads("nya")) == 0


def test_get_upload_round_trip(corpus_root: Path):
    from aiserver.corpus import add_upload, get_upload

    rec = add_upload("nya", b"DATA", {"filename_orig": "x.wav", "speaker_id": "s2"})
    fetched = get_upload("nya", rec["uuid"])
    assert fetched is not None
    assert fetched["uuid"] == rec["uuid"]
    assert fetched["speaker_id"] == "s2"


def test_get_upload_missing_returns_none(corpus_root: Path):
    from aiserver.corpus import get_upload

    assert get_upload("sna", "nonexistent-uuid") is None


def test_invalid_iso_rejected(corpus_root: Path):
    from aiserver.corpus import add_upload

    with pytest.raises(ValueError):
        add_upload("../etc/passwd", b"X", {})


def test_invalid_register_rejected(corpus_root: Path):
    from aiserver.corpus import add_upload

    with pytest.raises(ValueError):
        add_upload("sna", b"X", {"register": "spaceships"})


def test_meta_persists_across_module_reloads(corpus_root: Path):
    """Reload module to ensure data survives — caches must not hide state."""
    import importlib

    import aiserver.corpus as c

    c.add_upload("sna", b"PERSIST", {"filename_orig": "p.wav"})
    importlib.reload(c)
    rows = c.list_uploads("sna")
    assert len(rows) == 1
    assert rows[0]["filename_orig"] == "p.wav"
