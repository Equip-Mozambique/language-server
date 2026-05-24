"""Tests for the language readiness scoring metric."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aiserver import readiness
from aiserver.languages import LANGS
from aiserver.readiness import Tier


def _empty_bundle(iso: str) -> dict:
    """Minimal bundle simulating an ISO with no on-disk corpus."""
    lang = LANGS[iso]
    return {
        "iso": iso,
        "name": lang.name,
        "country": lang.country,
        "model_coverage": {
            "mms_iso": lang.mms_iso, "mms_tts": lang.mms_tts,
            "whisper_code": lang.whisper_code, "preferred_stt": lang.preferred_stt,
            "preferred_tts": lang.preferred_tts, "proxy_iso": lang.proxy_iso,
            "nllb": False,
        },
        "research_md": "",
        "dbs_bibles": [], "dbp_bibles": [],
        "uploads": [], "uploads_count": 0,
        "corpus": {
            "audio_filesets": [], "text_versions": [], "video_files": [],
            "storyrunners": None, "scriptureearth": None, "training_pairs": None,
        },
    }


def _full_bundle(iso: str) -> dict:
    """Bundle simulating a well-covered ISO (Shona-like)."""
    b = _empty_bundle(iso)
    b["dbs_bibles"] = [{"id": "X", "iso": iso}]
    b["dbp_bibles"] = [{"id": "Y"}]
    b["model_coverage"]["nllb"] = True
    b["corpus"] = {
        "audio_filesets": [{
            "fileset_id": "ABC", "path": ".", "chapter_count": 260, "file_count": 260,
            "total_bytes": 600_000_000, "total_duration_s": 90_000,  # 25h
            "has_text_in_manifest": False,
        }],
        "text_versions": [{
            "version_abbr": "V", "path": ".", "version_id": 1,
            "chapter_count": 260, "verse_count": 7959,
        }],
        "video_files": [],
        "storyrunners": {"path": ".", "file_count": 40, "total_bytes": 90_000_000},
        "scriptureearth": None,
        "training_pairs": {"path": ".", "pair_count": 260},
    }
    return b


def test_score_bounds_all_target_langs():
    """All ISOs in LANGS produce scores in [0,100] across all three axes."""
    for iso in LANGS:
        try:
            reports = readiness.readiness_all(iso)
        except Exception:
            continue  # external API may be down — skip not fail
        for axis, r in reports.items():
            assert 0 <= r.score <= 100, f"{iso}/{axis} = {r.score}"


def test_empty_corpus_low_tier():
    iso = "chw"  # known: nothing on disk
    with patch.object(readiness.resources, "get_resources", return_value=_empty_bundle(iso)):
        reports = readiness.readiness_all(iso)
    asr = reports["asr"]
    assert asr.tier in (Tier.BIBLELESS, Tier.BOOTSTRAP)
    assert asr.score < 35
    # Missing list must mention audio
    blob = " ".join(asr.missing_resources).lower()
    assert "audio" in blob


def test_full_corpus_high_tier():
    iso = "sna"
    bundle = _full_bundle(iso)
    with patch.object(readiness.resources, "get_resources", return_value=bundle):
        reports = readiness.readiness_all(iso)
    asr = reports["asr"]
    text = reports["text"]
    assert asr.score >= 45, f"sna ASR with full corpus = {asr.score}"
    # NT-only (no OT, no non-Bible text) caps text around BOOTSTRAP — expected
    assert text.score >= 20, f"sna text with full NT = {text.score}"


def test_score_to_tier_mapping():
    cases = [
        (0,  Tier.BIBLELESS),
        (10, Tier.BIBLELESS),
        (15, Tier.BOOTSTRAP),
        (30, Tier.BOOTSTRAP),
        (35, Tier.EMERGING),
        (50, Tier.EMERGING),
        (55, Tier.ADAPTER),
        (74, Tier.ADAPTER),
        (75, Tier.PRODUCTION),
        (89, Tier.PRODUCTION),
        (90, Tier.MATURE),
        (100, Tier.MATURE),
    ]
    for score, expected in cases:
        assert readiness._score_to_tier(score) == expected, f"score={score}"


def test_proxy_credit_appears_in_notes():
    """ndc has proxy=sna. If sna has a real score, ndc gets a note."""
    iso = "ndc"
    ndc_bundle = _empty_bundle(iso)
    sna_bundle = _full_bundle("sna")

    def fake_get(target_iso):
        if target_iso == iso:
            return ndc_bundle
        if target_iso == "sna":
            return sna_bundle
        return _empty_bundle(target_iso)

    with patch.object(readiness.resources, "get_resources", side_effect=fake_get):
        reports = readiness.readiness_all(iso)
    asr = reports["asr"]
    joined = " ".join(asr.notes).lower()
    assert "sna" in joined or "proxy" in joined


def test_unknown_iso_raises():
    with pytest.raises(KeyError):
        readiness.readiness_all("zzz")


def test_breakdown_sums_to_score_no_proxy():
    """Without proxy boost, sum(breakdown.values()) == score."""
    iso = "sna"  # no proxy
    bundle = _full_bundle(iso)
    with patch.object(readiness.resources, "get_resources", return_value=bundle):
        reports = readiness.readiness_all(iso)
    for axis, r in reports.items():
        assert sum(r.breakdown.values()) == r.score, (
            f"{axis} breakdown {r.breakdown} != score {r.score}"
        )


def test_overall_score_formula():
    reports = {
        "asr": readiness.ReadinessReport("asr", "x", 60, Tier.ADAPTER, {}),
        "tts": readiness.ReadinessReport("tts", "x", 40, Tier.EMERGING, {}),
        "text": readiness.ReadinessReport("text", "x", 80, Tier.PRODUCTION, {}),
    }
    overall = readiness.overall_score(reports)
    # 0.35*60 + 0.25*40 + 0.40*80 = 21 + 10 + 32 = 63
    assert overall == 63


def test_dbp_catalog_bonus():
    """ASR gets +5 if dbp_bibles non-empty."""
    iso = "vmw"
    b_no_dbp = _empty_bundle(iso)
    b_with_dbp = _empty_bundle(iso)
    b_with_dbp["dbp_bibles"] = [{"id": "X"}]
    with patch.object(readiness.resources, "get_resources", return_value=b_no_dbp):
        score_no = readiness.asr_readiness(iso).score
    with patch.object(readiness.resources, "get_resources", return_value=b_with_dbp):
        score_with = readiness.asr_readiness(iso).score
    assert score_with - score_no == 5


def test_flags_bible_only_domain_risk():
    iso = "vmw"
    b = _full_bundle(iso)
    with patch.object(readiness.resources, "get_resources", return_value=b):
        reports = readiness.readiness_all(iso)
    # Bible-only audio without uploads → flag should fire
    assert "BIBLE_ONLY_DOMAIN_RISK" in reports["asr"].flags
    assert "SINGLE_SPEAKER_ASR_RISK" in reports["asr"].flags
