"""Tests for the per-language resource aggregator."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture
def fake_dbs_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Build a minimal DBS catalog fixture and point the aggregator at it."""
    d = tmp_path / "bible_catalogs"
    d.mkdir()
    (d / "filtered_bibles.json").write_text(
        json.dumps(
            [
                {
                    "id": "SEHBSM",
                    "tt": "Chisena Bible",
                    "tv": "Cibverano Cipsa Cisena",
                    "iso": "seh",
                    "ln": "Sena",
                    "dt": "2017",
                    "cn": "Mozambique",
                },
                {
                    "id": "NDCNDC",
                    "tt": "Chindau New Bible",
                    "tv": "Bhaibheri Rakachena muChindau",
                    "iso": "ndc",
                    "ln": "Ndau",
                    "dt": "2015",
                    "cn": "Mozambique",
                },
            ]
        )
    )
    monkeypatch.setenv("AISERVER_BIBLE_CATALOGS", str(d))
    return d


@pytest.fixture
def fake_research_md(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    md = tmp_path / "RESEARCH.md"
    md.write_text(
        "# top\n\n"
        "## Per-Language Deep-Dive: Sena (seh)\n\n"
        "Sena is a Bantu language. ~1.5M speakers in Mozambique.\n\n"
        "## Per-Language Deep-Dive: Ndau (ndc)\n\n"
        "Ndau is closely related to Shona.\n\n"
        "## License Caveat\n\n"
        "MMS = CC-BY-NC 4.0.\n"
    )
    monkeypatch.setenv("AISERVER_RESEARCH_MD", str(md))
    return md


def test_resources_returns_full_shape(fake_dbs_dir, fake_research_md, corpus_root):
    from aiserver.resources import get_resources

    out = get_resources("seh")
    assert set(out.keys()) >= {
        "iso",
        "model_coverage",
        "research_md",
        "dbs_bibles",
        "uploads",
        "uploads_count",
    }
    assert out["iso"] == "seh"


def test_resources_model_coverage_from_registry(fake_dbs_dir, fake_research_md, corpus_root):
    from aiserver.resources import get_resources

    out = get_resources("seh")
    cov = out["model_coverage"]
    assert cov["mms_iso"] == "seh"
    assert cov["mms_tts"] == "seh"
    assert cov["whisper_code"] is None


def test_resources_dbs_filtered_for_iso(fake_dbs_dir, fake_research_md, corpus_root):
    from aiserver.resources import get_resources

    out = get_resources("seh")
    assert len(out["dbs_bibles"]) == 1
    assert out["dbs_bibles"][0]["id"] == "SEHBSM"

    out2 = get_resources("ndc")
    assert len(out2["dbs_bibles"]) == 1
    assert out2["dbs_bibles"][0]["id"] == "NDCNDC"


def test_resources_extracts_research_md_section(fake_dbs_dir, fake_research_md, corpus_root):
    from aiserver.resources import get_resources

    out = get_resources("seh")
    assert "Sena is a Bantu language" in out["research_md"]
    assert "License Caveat" not in out["research_md"]
    assert "Ndau is closely related" not in out["research_md"]


def test_resources_returns_empty_research_when_no_section(fake_dbs_dir, fake_research_md, corpus_root):
    from aiserver.resources import get_resources

    out = get_resources("sna")  # no Per-Language Deep-Dive: Shona in fixture
    assert out["research_md"] == ""


def test_resources_counts_uploads(fake_dbs_dir, fake_research_md, corpus_root):
    from aiserver.corpus import add_upload
    from aiserver.resources import get_resources

    add_upload("seh", b"A", {"filename_orig": "a.wav"})
    add_upload("seh", b"B", {"filename_orig": "b.wav"})
    add_upload("ndc", b"C", {"filename_orig": "c.wav"})

    out = get_resources("seh")
    assert out["uploads_count"] == 2
    assert len(out["uploads"]) == 2


def test_resources_unknown_iso_raises():
    from aiserver.resources import get_resources

    with pytest.raises(KeyError):
        get_resources("zzz")
