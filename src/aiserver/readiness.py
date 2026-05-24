"""Per-language readiness scoring across ASR / TTS / Text axes.

Consumes the on-disk corpus inventory from `resources.get_resources(iso)` and
emits three `ReadinessReport`s. Scoring uses saturating-knee functions anchored
to empirical thresholds for low-resource Bantu Bible-driven corpora.

Tier bands (applied to per-axis score 0-100):
  0-15  BIBLELESS
  15-35 BOOTSTRAP
  35-55 EMERGING
  55-75 ADAPTER
  75-90 PRODUCTION
  90-100 MATURE

Cross-lingual proxy credit: capped at 30% of axis score.
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

from . import resources
from .languages import LANGS, get


# Avg chars per Bible verse (sample across our Bantu NTs gave ~120-140; pick 130)
AVG_CHARS_PER_VERSE = 130

# StoryRunners quality multiplier on audio_h (studio + multi-lang aligned)
SR_QUALITY_MULTIPLIER = 1.5
# Rough seconds per StoryRunners mp3 file (most are 90-180s)
SR_AVG_SECS_PER_FILE = 150

# Tier cutoffs (descending)
_TIER_CUTOFFS = [
    (90, "MATURE"),
    (75, "PRODUCTION"),
    (55, "ADAPTER"),
    (35, "EMERGING"),
    (15, "BOOTSTRAP"),
    (0, "BIBLELESS"),
]


class Tier(str, Enum):
    BIBLELESS = "bibleless"
    BOOTSTRAP = "bootstrap"
    EMERGING = "emerging"
    ADAPTER = "adapter"
    PRODUCTION = "production"
    MATURE = "mature"


def _score_to_tier(score: int) -> Tier:
    for cutoff, name in _TIER_CUTOFFS:
        if score >= cutoff:
            return Tier[name]
    return Tier.BIBLELESS


@dataclass(frozen=True)
class ReadinessReport:
    axis: str                            # "asr" | "tts" | "text"
    iso: str
    score: int                            # 0-100
    tier: Tier
    breakdown: dict[str, int]             # named component → points (sum ≈ score)
    missing_resources: list[str] = field(default_factory=list)
    recommended_next_actions: list[str] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["tier"] = self.tier.value
        return d


def sat(x: float, knee: float) -> float:
    """Saturating-knee: x / (x + knee). 0 at x=0, 0.5 at x=knee, → 1 as x grows."""
    if x <= 0:
        return 0.0
    return x / (x + knee)


# ------------------------------- input extraction -------------------------------

def _audio_hours(corpus: dict) -> float:
    """Total audio hours across DBP, StoryRunners, ScriptureEarth."""
    h = 0.0
    for fs in corpus.get("audio_filesets") or []:
        h += (fs.get("total_duration_s") or 0) / 3600
    sr = corpus.get("storyrunners")
    if sr:
        # No durations stored — estimate
        h += SR_QUALITY_MULTIPLIER * (sr.get("file_count", 0) * SR_AVG_SECS_PER_FILE) / 3600
    se = corpus.get("scriptureearth")
    if se:
        # SE Makonde files are ~1-2min each; estimate 90s
        h += (se.get("file_count", 0) * 90) / 3600
    return h


def _align_bonus(corpus: dict) -> tuple[int, str]:
    """Returns (0/3/7/10, label). Higher = better alignment quality."""
    pairs = corpus.get("training_pairs")
    if pairs and pairs.get("pair_count", 0) > 0:
        # We have audio↔text paired at chapter level via Bible.com text
        return 7, "word_aeneas"  # treat as word-level proxy
    for fs in corpus.get("audio_filesets") or []:
        if fs.get("has_text_in_manifest"):
            return 3, "verse"
    return 0, "none"


def _speaker_count(bundle: dict) -> int:
    """Distinct speakers from uploads; default 1 if any Bible audio present."""
    uploads = bundle.get("uploads") or []
    speakers = {u.get("speaker_id") for u in uploads if u.get("speaker_id")}
    if speakers:
        return len(speakers)
    corpus = bundle.get("corpus") or {}
    if (corpus.get("audio_filesets") or corpus.get("storyrunners")
            or corpus.get("scriptureearth")):
        return 1
    return 0


def _audio_domain(bundle: dict) -> str:
    """'bible_only' unless uploads include non-religious registers."""
    uploads = bundle.get("uploads") or []
    registers = {(u.get("register") or "").lower() for u in uploads}
    non_religious = registers - {"", "religious", "read"}
    if non_religious:
        return "mixed"
    return "bible_only"


def _domain_diversity(bundle: dict) -> float:
    """Shannon entropy over upload registers, normalised to [0, 1]."""
    uploads = bundle.get("uploads") or []
    if not uploads:
        return 0.0
    regs = [u.get("register") or "religious" for u in uploads]
    counts = Counter(regs)
    total = sum(counts.values())
    if total == 0 or len(counts) <= 1:
        return 0.0
    h = -sum((c / total) * math.log(c / total, 2) for c in counts.values())
    h_max = math.log(len(counts), 2)
    return h / h_max if h_max > 0 else 0.0


def _text_chars(corpus: dict) -> int:
    """Total chars across all text_versions (verse_count * AVG_CHARS_PER_VERSE)."""
    chars = 0
    for tv in corpus.get("text_versions") or []:
        chars += tv.get("verse_count", 0) * AVG_CHARS_PER_VERSE
    return chars


def _parallel_sents(corpus: dict, bundle: dict) -> int:
    """Rough estimate of cross-lingual parallel sentences available."""
    n = 0
    sr = corpus.get("storyrunners")
    if sr:
        n += sr.get("file_count", 0) * 10  # ~10 sentences/story
    for u in bundle.get("uploads") or []:
        if u.get("transcript_path"):
            n += 1
    return n


# ------------------------------- scoring -------------------------------

def _build_corpus_view(iso: str, bundle: dict | None) -> tuple[dict, dict]:
    """Return (bundle, corpus). Fetches bundle if not supplied."""
    if bundle is None:
        bundle = resources.get_resources(iso)
    corpus = bundle.get("corpus") or {}
    return bundle, corpus


def _model_native_or_proxy(iso: str, native_attr: str) -> tuple[bool, str | None]:
    """Return (has_native, proxy_iso). native_attr e.g. 'mms_iso'."""
    lang = get(iso)
    if getattr(lang, native_attr):
        return True, None
    if lang.proxy_iso:
        proxy_lang = LANGS.get(lang.proxy_iso)
        if proxy_lang and getattr(proxy_lang, native_attr):
            return False, lang.proxy_iso
    return False, None


def _apply_proxy_boost(score: int, iso: str, axis: str) -> tuple[int, list[str]]:
    """Add up to 30% of proxy target's axis score; return (new_score, notes)."""
    lang = get(iso)
    if not lang.proxy_iso or lang.proxy_iso not in LANGS:
        return score, []
    # Recursive call to compute proxy target's score on same axis
    try:
        proxy_bundle = resources.get_resources(lang.proxy_iso)
    except Exception:
        return score, []
    if axis == "asr":
        target = asr_readiness(lang.proxy_iso, bundle=proxy_bundle)
    elif axis == "tts":
        target = tts_readiness(lang.proxy_iso, bundle=proxy_bundle)
    else:
        target = text_readiness(lang.proxy_iso, bundle=proxy_bundle)
    boost = int(0.3 * target.score)
    boosted = min(100, score + boost)
    notes = [
        f"+{boost} proxy credit from {lang.proxy_iso} ({axis}={target.score}). "
        f"Expect quality degradation vs native — Bantu-cluster transfer typically helps "
        f"5-10h worth of paired audio."
    ]
    return boosted, notes


# ------------------------------- ASR -------------------------------

def asr_readiness(iso: str, *, bundle: dict | None = None) -> ReadinessReport:
    bundle, corpus = _build_corpus_view(iso, bundle)
    lang = get(iso)

    audio_h = _audio_hours(corpus)
    align_pts, align_label = _align_bonus(corpus)
    speakers = _speaker_count(bundle)
    domain = _audio_domain(bundle)
    dbp_count = len(bundle.get("dbp_bibles") or [])

    breakdown: dict[str, int] = {}
    breakdown["audio_1h_floor"] = int(round(25 * sat(audio_h, 1)))
    breakdown["audio_10h"] = int(round(25 * sat(audio_h, 10)))
    breakdown["audio_50h"] = int(round(15 * sat(audio_h, 50)))
    breakdown["audio_200h"] = int(round(10 * sat(audio_h, 200)))
    breakdown["speakers"] = int(round(10 * min(speakers / 10, 1)))
    breakdown["alignment"] = align_pts
    breakdown["domain_mixed"] = 5 if domain != "bible_only" else 0
    breakdown["dbp_catalog"] = 5 if dbp_count >= 1 else 0
    score = min(100, sum(breakdown.values()))

    notes: list[str] = []
    score, proxy_notes = _apply_proxy_boost(score, iso, "asr")
    if proxy_notes:
        # Apply proxy boost as a real breakdown component for transparency
        boost = score - sum(breakdown.values())
        if boost > 0:
            breakdown["proxy_boost"] = boost
        notes.extend(proxy_notes)

    # Re-sum check (after proxy)
    score = min(100, sum(breakdown.values()))

    # Missing + actions
    missing: list[str] = []
    actions: list[str] = []
    if audio_h < 1:
        missing.append("No audio (< 1h)")
        if dbp_count > 0:
            actions.append(f"Run `python scripts/dbp_download.py {iso}` (DBP has {dbp_count} bibles)")
        else:
            actions.append("Search alternate sources (NCHLT, GRN, MMS-Lab)")
    elif audio_h < 10:
        missing.append(f"Limited audio ({audio_h:.1f}h, target ≥10h for WER<20)")
        actions.append("Pull StoryRunners + ScriptureEarth + JESUS Film audio")
    if align_pts == 0 and audio_h > 0:
        missing.append("No audio↔text alignment")
        actions.append("Run `python scripts/build_training_pairs.py` to align DBP audio w/ Bible.com text")
    if not lang.mms_iso and not lang.whisper_code:
        missing.append("No native ASR model")
        if lang.proxy_iso:
            actions.append(f"Use proxy={lang.proxy_iso}; fine-tune MMS adapter on collected pairs")
        else:
            actions.append("Train MMS adapter from related Bantu base")

    # Flags
    flags: list[str] = []
    if speakers <= 1 and audio_h > 0:
        flags.append("SINGLE_SPEAKER_ASR_RISK")
    if align_pts == 0:
        flags.append("NO_ALIGNMENT")
    if domain == "bible_only" and audio_h > 0:
        flags.append("BIBLE_ONLY_DOMAIN_RISK")

    return ReadinessReport(
        axis="asr",
        iso=iso,
        score=score,
        tier=_score_to_tier(score),
        breakdown=breakdown,
        missing_resources=missing,
        recommended_next_actions=actions,
        flags=flags,
        notes=notes,
    )


# ------------------------------- TTS -------------------------------

def tts_readiness(iso: str, *, bundle: dict | None = None) -> ReadinessReport:
    bundle, corpus = _build_corpus_view(iso, bundle)
    lang = get(iso)

    audio_h = _audio_hours(corpus)
    align_pts, _ = _align_bonus(corpus)
    speakers = _speaker_count(bundle)
    # Bible audio is generally studio-quality read speech
    studio = audio_h > 0

    breakdown: dict[str, int] = {}
    breakdown["audio_15min_floor"] = int(round(40 * sat(audio_h, 0.25)))
    breakdown["audio_2h"] = int(round(25 * sat(audio_h, 2)))
    breakdown["audio_20h"] = int(round(15 * sat(audio_h, 20)))
    breakdown["studio_quality"] = 10 if studio else 0
    breakdown["word_alignment"] = 5 if align_pts >= 7 else 0
    breakdown["multi_voice"] = int(round(5 * min(speakers / 3, 1)))
    score = min(100, sum(breakdown.values()))

    notes: list[str] = []
    score, proxy_notes = _apply_proxy_boost(score, iso, "tts")
    if proxy_notes:
        boost = score - sum(breakdown.values())
        if boost > 0:
            breakdown["proxy_boost"] = boost
        notes.extend(proxy_notes)
    score = min(100, sum(breakdown.values()))

    missing: list[str] = []
    actions: list[str] = []
    if audio_h < 0.25:
        missing.append("No clean studio audio (< 15 min)")
        actions.append("Pull Bible audio via DBP; even ~15 min unlocks MMS-TTS-style VITS training")
    elif audio_h < 2:
        missing.append(f"Marginal audio for FT ({audio_h*60:.0f} min, target ≥2h for XTTS/StyleTTS FT)")
    if not lang.mms_tts:
        missing.append("No native MMS-TTS checkpoint")
        if lang.proxy_iso and LANGS.get(lang.proxy_iso) and LANGS[lang.proxy_iso].mms_tts:
            actions.append(f"Fall back to MMS-TTS {lang.proxy_iso} or fine-tune VITS from sibling lang")
        else:
            actions.append("Use IMS Toucan (articulatory phonemes) + collect target audio")
    if speakers <= 1 and audio_h > 0:
        missing.append("Only 1 speaker — no multi-voice TTS possible")
        actions.append("Collect ≥2 additional speakers for voice diversity")

    flags: list[str] = []
    if speakers <= 1 and audio_h > 0:
        flags.append("SINGLE_SPEAKER_TTS_RISK")

    return ReadinessReport(
        axis="tts",
        iso=iso,
        score=score,
        tier=_score_to_tier(score),
        breakdown=breakdown,
        missing_resources=missing,
        recommended_next_actions=actions,
        flags=flags,
        notes=notes,
    )


# ------------------------------- Text / LM -------------------------------

def text_readiness(iso: str, *, bundle: dict | None = None) -> ReadinessReport:
    bundle, corpus = _build_corpus_view(iso, bundle)
    lang = get(iso)

    chars = _text_chars(corpus)
    diversity = _domain_diversity(bundle)
    parallel = _parallel_sents(corpus, bundle)
    nllb = (bundle.get("model_coverage") or {}).get("nllb", False)

    breakdown: dict[str, int] = {}
    breakdown["text_nt"] = int(round(20 * sat(chars, 500_000)))
    breakdown["text_whole_bible"] = int(round(25 * sat(chars, 3_000_000)))
    breakdown["text_news_wiki"] = int(round(20 * sat(chars, 20_000_000)))
    breakdown["text_diverse"] = int(round(15 * sat(chars, 200_000_000)))
    breakdown["domain_diversity"] = int(round(15 * diversity))
    breakdown["parallel_pivot"] = int(round(5 * sat(parallel, 10_000)))
    # Bonus for NLLB native (model already trained on this lang)
    if nllb:
        breakdown["nllb_native"] = 5
    score = min(100, sum(breakdown.values()))

    notes: list[str] = []
    score, proxy_notes = _apply_proxy_boost(score, iso, "text")
    if proxy_notes:
        boost = score - sum(breakdown.values())
        if boost > 0:
            breakdown["proxy_boost"] = boost
        notes.extend(proxy_notes)
    score = min(100, sum(breakdown.values()))

    missing: list[str] = []
    actions: list[str] = []
    if chars == 0:
        missing.append("No vernacular text on disk")
        actions.append(f"Run `python scripts/biblecom_download.py download-cmd {iso}` (or check alt ISO)")
    elif chars < 500_000:
        missing.append(f"Below tokenizer threshold ({chars:,} chars; target ≥500k)")
        actions.append("Pull additional Bible versions or non-Bible text")
    elif chars < 3_000_000:
        missing.append("NT-only — OT would 3× chars + add genre diversity")
        actions.append("Source OT translation if available; pull from DBS / Bible Societies")
    if not nllb:
        missing.append("Not in NLLB-200 — limited MT")
        if lang.proxy_iso and LANGS.get(lang.proxy_iso):
            actions.append(f"Use NLLB pivot via proxy={lang.proxy_iso}")
    if diversity < 0.2:
        missing.append("Single-register corpus (Bible-only)")
        actions.append("Collect news / wiki / conversational text — biggest LM-quality unlock")

    flags: list[str] = []
    if diversity < 0.2:
        flags.append("BIBLE_ONLY_DOMAIN_RISK")
    if chars < 300_000:
        flags.append("TOKENIZER_STARVED")
    if parallel < 1_000_000:
        flags.append("BELOW_NLLB_HR")

    return ReadinessReport(
        axis="text",
        iso=iso,
        score=score,
        tier=_score_to_tier(score),
        breakdown=breakdown,
        missing_resources=missing,
        recommended_next_actions=actions,
        flags=flags,
        notes=notes,
    )


# ------------------------------- public ----------------------------------

def readiness_all(iso: str) -> dict[str, ReadinessReport]:
    """Compute all three axes. One get_resources() call per axis (shared)."""
    bundle = resources.get_resources(iso)
    return readiness_all_from_bundle(iso, bundle)


def readiness_all_from_bundle(iso: str, bundle: dict) -> dict[str, ReadinessReport]:
    """Same as `readiness_all` but caller provides bundle (avoids double DBP fetch)."""
    return {
        "asr": asr_readiness(iso, bundle=bundle),
        "tts": tts_readiness(iso, bundle=bundle),
        "text": text_readiness(iso, bundle=bundle),
    }


def overall_score(reports: dict[str, ReadinessReport]) -> int:
    """Weighted overall: 0.35 ASR + 0.25 TTS + 0.40 Text."""
    return int(round(
        0.35 * reports["asr"].score
        + 0.25 * reports["tts"].score
        + 0.40 * reports["text"].score
    ))
