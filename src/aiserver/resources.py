"""Per-language resource aggregator.

Combines: registry model coverage flags + DBS Bible catalog hits + RESEARCH.md
deep-dive section + uploaded corpus contents.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from . import corpus
from .languages import get


_DEEP_DIVE_RE = re.compile(
    r"^##\s+Per-Language Deep-Dive:\s+[^()]+\((?P<iso>[a-z]{2,3})\)\s*$",
    re.MULTILINE,
)


def _bible_catalogs_dir() -> Path:
    env = os.environ.get("AISERVER_BIBLE_CATALOGS")
    if env:
        return Path(env)
    return Path.home() / "ai-server" / "data" / "research" / "bible_catalogs"


def _research_md_path() -> Path:
    env = os.environ.get("AISERVER_RESEARCH_MD")
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[2] / "RESEARCH.md"


def _load_dbs_filtered() -> dict[str, list[dict[str, Any]]]:
    path = _bible_catalogs_dir() / "filtered_bibles.json"
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text())
    except json.JSONDecodeError:
        return {}
    grouped: dict[str, list[dict[str, Any]]] = {}
    for b in raw:
        iso = b.get("iso")
        if iso:
            grouped.setdefault(iso, []).append(b)
    return grouped


def _next_section_pos(text: str, from_pos: int) -> int:
    m = re.search(r"^##\s+", text[from_pos:], re.MULTILINE)
    return from_pos + m.start() if m else len(text)


def _extract_research_section(iso: str) -> str:
    path = _research_md_path()
    if not path.exists():
        return ""
    text = path.read_text()
    matches = list(_DEEP_DIVE_RE.finditer(text))
    for i, m in enumerate(matches):
        if m.group("iso") == iso:
            start = m.start()
            if i + 1 < len(matches):
                end = matches[i + 1].start()
            else:
                end = _next_section_pos(text, m.end())
            return text[start:end].rstrip() + "\n"
    return ""


def _dbp_bibles_for(iso: str) -> list[dict[str, Any]]:
    """Fetch DBP audio Bibles. Silently empty if no API key or network fails."""
    try:
        from . import dbp

        bibles = dbp.list_bibles(language_code=iso, media="audio", limit=50)
    except Exception:
        return []
    out: list[dict[str, Any]] = []
    for b in bibles:
        filesets = [
            {
                "id": fs.fileset_id,
                "label": f"{fs.set_size_code} · {fs.set_type_code}"
                + (f" · {fs.bitrate} kbps" if fs.bitrate else ""),
                "type": fs.set_type_code,
                "scope": fs.set_size_code,
                "bitrate": fs.bitrate,
                "asset_id": fs.asset_id,
                "codec": fs.codec,
            }
            for fs in b.filesets
            if "audio" in (fs.set_type_code or "")
        ]
        if not filesets:
            continue
        out.append(
            {
                "id": b.id,
                "name": b.name_english or b.id,
                "name_vernacular": b.name_vernacular,
                "scope": filesets[0]["scope"],
                "filesets": filesets,
            }
        )
    return out


def get_resources(iso: str) -> dict[str, Any]:
    lang = get(iso)
    dbs_grouped = _load_dbs_filtered()
    uploads = corpus.list_uploads(iso)
    bundle = {
        "iso": iso,
        "name": lang.name,
        "country": lang.country,
        "model_coverage": {
            "mms_iso": lang.mms_iso,
            "mms_tts": lang.mms_tts,
            "whisper_code": lang.whisper_code,
            "preferred_stt": lang.preferred_stt,
            "preferred_tts": lang.preferred_tts,
            "proxy_iso": lang.proxy_iso,
            "nllb": _has_nllb(iso),
        },
        "research_md": _extract_research_section(iso),
        "dbs_bibles": dbs_grouped.get(iso, []),
        "dbp_bibles": _dbp_bibles_for(iso),
        "uploads": uploads,
        "uploads_count": len(uploads),
        "corpus": _scan_corpus(iso),
    }
    # Additive: embed readiness so the SPA gets it in one request.
    # Imported lazily to avoid circular import (readiness imports resources).
    try:
        from . import readiness as _readiness
        reports = _readiness.readiness_all_from_bundle(iso, bundle)
        bundle["readiness"] = {axis: r.as_dict() for axis, r in reports.items()}
        bundle["readiness"]["overall"] = _readiness.overall_score(reports)
    except Exception:
        # Never let readiness scoring break the resources endpoint
        bundle["readiness"] = None
    return bundle


def _scan_corpus(iso: str) -> dict[str, Any]:
    """Enumerate on-disk downloaded resources for this ISO under data/."""
    root = Path.home() / "ai-server" / "data"
    iso_audio = root / "audio" / iso
    iso_text = root / "text" / iso
    iso_video = root / "video" / iso
    iso_pairs = root / "pairs" / iso

    audio_filesets: list[dict[str, Any]] = []
    storyrunners: dict[str, Any] | None = None
    scriptureearth: dict[str, Any] | None = None
    if iso_audio.exists():
        for sub in sorted(iso_audio.iterdir()):
            if not sub.is_dir():
                continue
            if sub.name == "storyrunners":
                ext = sub / "extracted"
                if ext.exists():
                    mp3s = [p for p in ext.rglob("*.mp3") if "__MACOSX" not in str(p)]
                    storyrunners = {
                        "path": str(ext.relative_to(root)),
                        "file_count": len(mp3s),
                        "total_bytes": sum(p.stat().st_size for p in mp3s),
                    }
                continue
            if sub.name == "scriptureearth":
                mp3s = list(sub.rglob("*.mp3"))
                scriptureearth = {
                    "path": str(sub.relative_to(root)),
                    "file_count": len(mp3s),
                    "total_bytes": sum(p.stat().st_size for p in mp3s),
                }
                continue
            manifest = sub / "manifest.json"
            if manifest.exists():
                try:
                    m = json.loads(manifest.read_text())
                    audio_files = list(sub.glob("*.mp3")) + list(sub.glob("*.webm"))
                    total_dur = sum((e.get("duration_s") or 0) for e in m) if isinstance(m, list) else 0
                    audio_filesets.append({
                        "fileset_id": sub.name,
                        "path": str(sub.relative_to(root)),
                        "chapter_count": len(m) if isinstance(m, list) else 0,
                        "file_count": len(audio_files),
                        "total_bytes": sum(p.stat().st_size for p in audio_files),
                        "total_duration_s": total_dur,
                        "has_text_in_manifest": any(e.get("text") for e in m) if isinstance(m, list) else False,
                    })
                except Exception:
                    pass

    text_versions: list[dict[str, Any]] = []
    if iso_text.exists():
        for sub in sorted(iso_text.iterdir()):
            if not sub.is_dir():
                continue
            nt_manifest = sub / "nt_manifest.json"
            if nt_manifest.exists():
                try:
                    m = json.loads(nt_manifest.read_text())
                    chapters = m.get("chapters", {})
                    verse_count = sum(len(v) for v in chapters.values())
                    text_versions.append({
                        "version_abbr": sub.name,
                        "path": str(nt_manifest.relative_to(root)),
                        "version_id": m.get("version_id"),
                        "chapter_count": len(chapters),
                        "verse_count": verse_count,
                    })
                except Exception:
                    pass

    video_files: list[dict[str, Any]] = []
    if iso_video.exists():
        for sub in sorted(iso_video.iterdir()):
            if not sub.is_dir():
                continue
            for vf in sorted(sub.glob("*.mp4")):
                video_files.append({
                    "source": sub.name,
                    "name": vf.name,
                    "path": str(vf.relative_to(root)),
                    "bytes": vf.stat().st_size,
                })

    training_pairs: dict[str, Any] | None = None
    pairs_file = iso_pairs / "pairs.jsonl"
    if pairs_file.exists():
        try:
            with pairs_file.open() as f:
                lines = sum(1 for _ in f)
        except Exception:
            lines = 0
        training_pairs = {
            "path": str(pairs_file.relative_to(root)),
            "pair_count": lines,
        }

    return {
        "audio_filesets": audio_filesets,
        "text_versions": text_versions,
        "video_files": video_files,
        "storyrunners": storyrunners,
        "scriptureearth": scriptureearth,
        "training_pairs": training_pairs,
    }


def _has_nllb(iso: str) -> bool:
    """Whether the language has any NLLB-200 FLORES code wired up."""
    try:
        from .translate import NLLB_CODES

        return NLLB_CODES.get(iso) is not None
    except Exception:
        return False
