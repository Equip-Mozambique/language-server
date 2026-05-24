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


def get_resources(iso: str) -> dict[str, Any]:
    lang = get(iso)
    dbs_grouped = _load_dbs_filtered()
    uploads = corpus.list_uploads(iso)
    return {
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
        },
        "research_md": _extract_research_section(iso),
        "dbs_bibles": dbs_grouped.get(iso, []),
        "uploads": uploads,
        "uploads_count": len(uploads),
    }
