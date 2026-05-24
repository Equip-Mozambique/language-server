"""Arclight / Jesus Film Project public REST API client.

Base: https://api.arclight.org/v2/
No API key required. Powers jesusfilm.org. Returns direct mux.com mp4 + HLS URLs.

Key endpoints:
- /media-languages?term=<name>             -> search by language name
- /media-languages?ids=<id>                -> language details
- /media-components?languageIds=<id>        -> list videos for language
- /media-components/<componentId>/languages/<languageId>  -> mp4 URLs

Common content (mediaComponentId):
- 1_jf-0-0   JESUS Film (~2hr, 61 segments)
- 1_mld-0-0  Magdalena (~44 segments)
- 1_cl-0-0   Story of Jesus for Children
- 1_jf6101-0-0 family  Lumo Gospels (per-Gospel)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


BASE_URL = "https://api.arclight.org/v2"
DEFAULT_TIMEOUT = 30.0


@dataclass(frozen=True)
class MediaLanguage:
    language_id: int
    iso639_3: str
    name: str
    native_name: str


@dataclass(frozen=True)
class MediaComponent:
    component_id: str
    title: str
    sub_type: str          # featureFilm | shortFilm | series | segment
    length_ms: int
    is_downloadable: bool
    image_url: str | None


def _client() -> httpx.Client:
    return httpx.Client(base_url=BASE_URL, timeout=DEFAULT_TIMEOUT, follow_redirects=True)


def search_languages(term: str) -> list[MediaLanguage]:
    """Search for a language by English or native name."""
    with _client() as c:
        r = c.get("/media-languages", params={"term": term, "limit": 50})
        r.raise_for_status()
        data = r.json()
    items = data.get("_embedded", {}).get("mediaLanguages") or data.get("mediaLanguages") or []
    out = []
    for it in items:
        out.append(MediaLanguage(
            language_id=int(it.get("languageId") or it.get("id") or 0),
            iso639_3=it.get("iso3", "") or it.get("bcp47", ""),
            name=it.get("name", ""),
            native_name=it.get("nameNative", "") or it.get("name", ""),
        ))
    return out


def get_language(language_id: int) -> dict[str, Any]:
    """Fetch a single language metadata blob."""
    with _client() as c:
        r = c.get(f"/media-languages/{language_id}")
        r.raise_for_status()
        return r.json()


def list_components(language_id: int, *, limit: int = 200) -> list[MediaComponent]:
    """List media-components (videos) available in a given language."""
    with _client() as c:
        r = c.get("/media-components", params={"languageIds": language_id, "limit": limit})
        r.raise_for_status()
        data = r.json()
    items = data.get("_embedded", {}).get("mediaComponents") or data.get("mediaComponents") or []
    out = []
    for it in items:
        out.append(MediaComponent(
            component_id=it.get("mediaComponentId", ""),
            title=it.get("title", ""),
            sub_type=it.get("subType", ""),
            length_ms=int(it.get("lengthInMilliseconds") or 0),
            is_downloadable=bool(it.get("isDownloadable", False)),
            image_url=(it.get("imageUrls", {}) or {}).get("mobileCinematicHigh"),
        ))
    return out


def get_component_for_language(component_id: str, language_id: int) -> dict[str, Any]:
    """Return full media-component-for-language record incl. mux URLs."""
    with _client() as c:
        r = c.get(f"/media-components/{component_id}/languages/{language_id}")
        r.raise_for_status()
        return r.json()


def video_urls(component_id: str, language_id: int) -> dict[str, str]:
    """Extract direct mp4 + HLS URLs for a (component, language) pair.

    Returns dict keyed by quality: '270p', '720p', 'hls', etc.
    """
    rec = get_component_for_language(component_id, language_id)
    urls: dict[str, str] = {}

    # Look in downloadUrls (most reliable) and streamingUrls
    for url in rec.get("downloadUrls", {}).values() if isinstance(rec.get("downloadUrls"), dict) else []:
        if isinstance(url, dict):
            urls[url.get("quality", "unknown")] = url.get("url", "")

    streaming = rec.get("streamingUrls", {}) or {}
    if isinstance(streaming, dict):
        for key, val in streaming.items():
            if isinstance(val, list) and val:
                first = val[0]
                if isinstance(first, dict):
                    urls[f"stream_{key}"] = first.get("url") or first.get("href", "")
            elif isinstance(val, dict):
                urls[f"stream_{key}"] = val.get("url", "")
            elif isinstance(val, str):
                urls[f"stream_{key}"] = val

    # Also pull from any "downloads" array
    for d in rec.get("downloads") or []:
        if isinstance(d, dict):
            urls[d.get("quality", "download")] = d.get("url", "")

    return {k: v for k, v in urls.items() if v}


def find_film(language_id: int, name_substring: str) -> MediaComponent | None:
    """Convenience: find component whose title contains substring (case-insensitive)."""
    components = list_components(language_id)
    needle = name_substring.lower()
    for c in components:
        if needle in c.title.lower():
            return c
    return None
