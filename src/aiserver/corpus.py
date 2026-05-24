"""Upload corpus storage: per-language folder + sqlite metadata.

Layout:
  <root>/<iso>/raw/<uuid>.<ext>
  <root>/<iso>/meta.sqlite

Root is `$AISERVER_CORPUS_ROOT` or `~/ai-server/data/uploads`. Each ISO has its
own sqlite DB so concurrent writes to different languages don't contend, and a
language's corpus can be moved or backed up independently.

SHA256 over the file bytes is the dedup key — re-uploading the same payload
returns the original UUID.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import os
import re
import sqlite3
import uuid as _uuid
from pathlib import Path
from typing import Any

from .languages import LANGS

VALID_REGISTERS = {"read", "conversational", "news", "religious", "code-switch", "other"}
VALID_LICENSES = {"CC-BY", "CC-BY-NC", "CC0", "proprietary", "unknown"}

_ISO_RE = re.compile(r"^[a-z]{2,3}$")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS files (
    uuid TEXT PRIMARY KEY,
    iso TEXT NOT NULL,
    filename_orig TEXT,
    path TEXT NOT NULL,
    media_type TEXT,
    duration_s REAL,
    speaker_id TEXT,
    dialect TEXT,
    register TEXT,
    license TEXT,
    transcript TEXT,
    transcript_path TEXT,
    uploaded_at TEXT NOT NULL,
    sha256 TEXT NOT NULL UNIQUE
);
CREATE INDEX IF NOT EXISTS files_sha_idx ON files(sha256);
"""


def _root() -> Path:
    env = os.environ.get("AISERVER_CORPUS_ROOT")
    if env:
        return Path(env)
    return Path.home() / "ai-server" / "data" / "uploads"


def _validate_iso(iso: str) -> str:
    if not _ISO_RE.fullmatch(iso):
        raise ValueError(f"invalid ISO code: {iso!r}")
    if iso not in LANGS:
        raise ValueError(f"unknown language: {iso!r}")
    return iso


def _iso_dir(iso: str) -> Path:
    d = _root() / iso
    (d / "raw").mkdir(parents=True, exist_ok=True)
    return d


def _db(iso: str) -> sqlite3.Connection:
    db_path = _iso_dir(iso) / "meta.sqlite"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    return conn


def _guess_ext(media_type: str | None, filename_orig: str | None) -> str:
    if filename_orig:
        suf = Path(filename_orig).suffix.lower()
        if suf in {".wav", ".mp3", ".flac", ".ogg", ".webm", ".m4a", ".txt", ".srt", ".vtt"}:
            return suf
    if media_type:
        if media_type.startswith("audio/"):
            return "." + media_type.split("/", 1)[1].split(";")[0]
        if media_type.startswith("text/"):
            return ".txt"
    return ".bin"


def add_upload(iso: str, payload: bytes, meta: dict[str, Any]) -> dict[str, Any]:
    """Persist `payload` and `meta` for `iso`. Returns the stored row as a dict.

    Dedup: same SHA256 → returns existing row (does not re-write).
    """
    iso = _validate_iso(iso)

    register = meta.get("register")
    if register is not None and register not in VALID_REGISTERS:
        raise ValueError(f"invalid register: {register!r}")
    license_ = meta.get("license")
    if license_ is not None and license_ not in VALID_LICENSES:
        raise ValueError(f"invalid license: {license_!r}")

    sha = hashlib.sha256(payload).hexdigest()

    with _db(iso) as conn:
        existing = conn.execute("SELECT * FROM files WHERE sha256=?", (sha,)).fetchone()
        if existing:
            return dict(existing)

        uid = _uuid.uuid4().hex
        ext = _guess_ext(meta.get("media_type"), meta.get("filename_orig"))
        stored = _iso_dir(iso) / "raw" / f"{uid}{ext}"
        stored.write_bytes(payload)

        row = {
            "uuid": uid,
            "iso": iso,
            "filename_orig": meta.get("filename_orig"),
            "path": str(stored),
            "media_type": meta.get("media_type"),
            "duration_s": meta.get("duration_s"),
            "speaker_id": meta.get("speaker_id"),
            "dialect": meta.get("dialect"),
            "register": register,
            "license": license_,
            "transcript": meta.get("transcript"),
            "transcript_path": meta.get("transcript_path"),
            "uploaded_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
            "sha256": sha,
        }
        conn.execute(
            """INSERT INTO files (uuid, iso, filename_orig, path, media_type, duration_s,
                                  speaker_id, dialect, register, license, transcript,
                                  transcript_path, uploaded_at, sha256)
               VALUES (:uuid, :iso, :filename_orig, :path, :media_type, :duration_s,
                       :speaker_id, :dialect, :register, :license, :transcript,
                       :transcript_path, :uploaded_at, :sha256)""",
            row,
        )
    return row


def list_uploads(iso: str) -> list[dict[str, Any]]:
    iso = _validate_iso(iso)
    db_path = _root() / iso / "meta.sqlite"
    if not db_path.exists():
        return []
    with _db(iso) as conn:
        rows = conn.execute("SELECT * FROM files ORDER BY uploaded_at DESC").fetchall()
    return [dict(r) for r in rows]


def get_upload(iso: str, uuid: str) -> dict[str, Any] | None:
    iso = _validate_iso(iso)
    db_path = _root() / iso / "meta.sqlite"
    if not db_path.exists():
        return None
    with _db(iso) as conn:
        row = conn.execute("SELECT * FROM files WHERE uuid=?", (uuid,)).fetchone()
    return dict(row) if row else None
