"""Digital Bible Platform (DBP) v4 API client.

API key required. Get one from FCBH:
  https://www.faithcomesbyhearing.com/audio-bible-resources/developer-documentation

Set in environment as DBP_API_KEY, either via shell rc or .env file at project root.

Useful endpoints:
- /bibles                       list bibles (filter by language_code, country, media)
- /bibles/{bible_id}            get bible metadata + filesets
- /bibles/filesets/{fileset_id} list chapters in fileset (audio or text)
- /bibles/filesets/{fileset_id}/{book}/{chapter}?asset_id=<cdn>
                                get audio file URLs for a chapter
- /languages                    list languages
- /countries/{iso}              get country metadata
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv


BASE_URL = "https://4.dbt.io/api"

# Load .env at project root if present
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_PROJECT_ROOT / ".env")


def _key() -> str:
    k = os.getenv("DBP_API_KEY")
    if not k:
        raise RuntimeError(
            "DBP_API_KEY not set. Either:\n"
            "  echo 'DBP_API_KEY=yourkey' > ~/ai-server/.env\n"
            "  OR add `export DBP_API_KEY=...` to ~/.bashrc and re-source"
        )
    return k


@dataclass(frozen=True)
class Fileset:
    fileset_id: str
    set_type_code: str  # audio | audio_drama | text_plain | text_usx | ...
    set_size_code: str  # NT | OT | C (complete) | P (portions) | NTOTP | ...
    bitrate: str | None
    asset_id: str | None
    codec: str | None


@dataclass(frozen=True)
class Bible:
    id: str
    language_code: str          # ISO 639-3
    language_name: str
    name_vernacular: str        # e.g. "Bhaibheri Rakachena muChindau"
    name_english: str
    filesets: list[Fileset]


def _client() -> httpx.Client:
    return httpx.Client(
        base_url=BASE_URL,
        params={"v": 4, "key": _key()},
        timeout=30.0,
        headers={"Accept": "application/json"},
    )


def list_bibles(
    *,
    language_code: str | None = None,
    country: str | None = None,
    media: str | None = None,
    limit: int = 200,
) -> list[Bible]:
    """List bibles filtered by language ISO-639-3 / country ISO-2 / media type."""
    params: dict[str, Any] = {"limit": limit}
    if language_code:
        params["language_code"] = language_code
    if country:
        params["country"] = country
    if media:
        params["media"] = media

    with _client() as c:
        r = c.get("/bibles", params=params)
        r.raise_for_status()
        data = r.json()["data"]

    bibles: list[Bible] = []
    for row in data:
        filesets_raw = row.get("filesets", {})
        all_fs: list[Fileset] = []
        for asset_id, group in filesets_raw.items():
            for fs in group:
                all_fs.append(
                    Fileset(
                        fileset_id=fs["id"],
                        set_type_code=fs.get("type", ""),
                        set_size_code=fs.get("size", ""),
                        bitrate=fs.get("bitrate"),
                        asset_id=asset_id,
                        codec=fs.get("codec"),
                    )
                )
        bibles.append(
            Bible(
                id=row["abbr"],
                language_code=row.get("language_id", "") or row.get("iso", ""),
                language_name=row.get("language", ""),
                name_vernacular=row.get("vname", "") or "",
                name_english=row.get("name", ""),
                filesets=all_fs,
            )
        )
    return bibles


def fileset_chapters(fileset_id: str, asset_id: str | None = None) -> list[dict]:
    """List chapters/files in an audio fileset with timing + URL info."""
    params: dict[str, Any] = {}
    if asset_id:
        params["asset_id"] = asset_id
    with _client() as c:
        r = c.get(f"/bibles/filesets/{fileset_id}", params=params)
        r.raise_for_status()
        return r.json()["data"]


def chapter_files(
    fileset_id: str,
    book: str,
    chapter: int,
    asset_id: str | None = None,
) -> list[dict]:
    """Get downloadable file URLs for a specific chapter."""
    params: dict[str, Any] = {}
    if asset_id:
        params["asset_id"] = asset_id
    with _client() as c:
        r = c.get(f"/bibles/filesets/{fileset_id}/{book}/{chapter}", params=params)
        r.raise_for_status()
        return r.json()["data"]


def text_plain(fileset_id: str) -> list[dict]:
    """Fetch plain-text Bible content as list of verses (book, chapter, verse, text)."""
    with _client() as c:
        r = c.get(f"/bibles/filesets/{fileset_id}")
        r.raise_for_status()
        return r.json()["data"]


def download_file(url: str, dest: Path, *, chunk: int = 1 << 16) -> int:
    """Stream URL to disk. Returns bytes written."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    bytes_written = 0
    with httpx.stream("GET", url, timeout=120.0, follow_redirects=True) as r:
        r.raise_for_status()
        with dest.open("wb") as f:
            for blk in r.iter_bytes(chunk):
                f.write(blk)
                bytes_written += len(blk)
    return bytes_written
