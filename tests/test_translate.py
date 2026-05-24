"""Tests for hybrid translation routing (Whisper translate + NLLB)."""

from __future__ import annotations

import pytest


def test_nllb_codes_has_expected_langs():
    from aiserver.translate import NLLB_CODES

    # Languages that ARE in NLLB 200 (FLORES code present)
    assert NLLB_CODES.get("sna") == "sna_Latn"
    assert NLLB_CODES.get("nya") == "nya_Latn"
    assert NLLB_CODES.get("tso") == "tso_Latn"
    assert NLLB_CODES.get("por") == "por_Latn"
    # Languages NOT in NLLB
    assert NLLB_CODES.get("seh") is None
    assert NLLB_CODES.get("ndc") is None
    assert NLLB_CODES.get("kck") is None
    assert NLLB_CODES.get("chw") is None


def test_route_decision_whisper_translate_for_supported_src_to_en():
    """sna→en should route to whisper-translate (special audio-level path)."""
    from aiserver.translate import plan_translation

    plan = plan_translation(src_iso="sna", tgt="en")
    assert plan["engine"] == "whisper-translate"
    assert plan["covered"] is True


def test_route_decision_nllb_for_sna_to_pt():
    """Whisper translate only does English. Portuguese target → NLLB."""
    from aiserver.translate import plan_translation

    plan = plan_translation(src_iso="sna", tgt="pt")
    assert plan["engine"] == "nllb"
    assert plan["covered"] is True


def test_route_decision_none_for_uncovered_src():
    """Sena has no Whisper and no NLLB coverage."""
    from aiserver.translate import plan_translation

    plan = plan_translation(src_iso="seh", tgt="en")
    assert plan["engine"] == "none"
    assert plan["covered"] is False


def test_route_decision_nllb_for_nya_to_pt():
    from aiserver.translate import plan_translation

    plan = plan_translation(src_iso="nya", tgt="pt")
    assert plan["engine"] == "nllb"
    assert plan["covered"] is True


def test_translate_text_with_uncovered_lang_returns_passthrough():
    """When neither engine covers the pair, return source text + covered=False."""
    from aiserver.translate import translate_text

    out = translate_text("ndzandzala", src_iso="seh", tgt="en")
    assert out["engine"] == "none"
    assert out["covered"] is False
    assert out["text"] == ""


def test_translate_text_with_nllb_calls_underlying_model(monkeypatch):
    """When NLLB is the chosen engine, translate_text must call the NLLB stub."""
    import aiserver.translate as t

    calls = []

    def fake_nllb_translate(text, src_flores, tgt_flores):
        calls.append((text, src_flores, tgt_flores))
        return "MOCK_TRANSLATION"

    monkeypatch.setattr(t, "_nllb_translate", fake_nllb_translate)
    out = t.translate_text("Mhoroi", src_iso="sna", tgt="pt")
    assert out["engine"] == "nllb"
    assert out["covered"] is True
    assert out["text"] == "MOCK_TRANSLATION"
    assert calls == [("Mhoroi", "sna_Latn", "por_Latn")]


def test_translate_text_to_english_for_nllb_supported_lang(monkeypatch):
    """sna→en is whisper-translate territory (uses audio). Text-only path falls back to NLLB."""
    import aiserver.translate as t

    monkeypatch.setattr(t, "_nllb_translate", lambda x, s, tgt: "Hello")
    out = t.translate_text("Mhoroi", src_iso="sna", tgt="en")
    # For text-only translation (no audio), prefer NLLB since whisper-translate needs audio.
    assert out["engine"] == "nllb"
    assert out["text"] == "Hello"
