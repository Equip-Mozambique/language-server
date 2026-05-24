"""Bible.com / YouVersion scraper for vernacular Bible text.

Bible.com URL pattern:
  https://www.bible.com/languages/<iso>            -> list of versions
  https://www.bible.com/bible/<version_id>/<BOOK>.<chapter>.<abbr>  -> chapter

We extract verses from rendered HTML (the chapter page is server-rendered with
verse text in <span class="verse vN">...</span> structure).
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from typing import Iterator

from bs4 import BeautifulSoup

from .scrape import scrape, ScrapeError


BASE = "https://www.bible.com"
DEFAULT_DELAY = 0.3  # be polite

# NT book codes with chapter counts (USFM 3-letter codes, FCBH order)
NT_BOOKS: list[tuple[str, int]] = [
    ("MAT", 28), ("MRK", 16), ("LUK", 24), ("JHN", 21),
    ("ACT", 28), ("ROM", 16), ("1CO", 16), ("2CO", 13),
    ("GAL", 6), ("EPH", 6), ("PHP", 4), ("COL", 4),
    ("1TH", 5), ("2TH", 3), ("1TI", 6), ("2TI", 4),
    ("TIT", 3), ("PHM", 1), ("HEB", 13), ("JAS", 5),
    ("1PE", 5), ("2PE", 3), ("1JN", 5), ("2JN", 1),
    ("3JN", 1), ("JUD", 1), ("REV", 22),
]
# Total chapters: 260


@dataclass(frozen=True)
class Version:
    id: int
    abbr: str
    local_abbr: str
    title: str
    local_title: str
    publisher: str | None


def list_versions(iso: str) -> list[Version]:
    """List Bible versions on bible.com for given ISO 639-3 code."""
    url = f"{BASE}/languages/{iso}"
    res = scrape(url, only=["httpx", "curl_cffi"])
    m = re.search(r"__NEXT_DATA__[^>]*>(\{.+?\})</script>", res.html, re.DOTALL)
    if not m:
        return []
    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError:
        return []

    versions_raw = _find_versions(data)
    if not versions_raw:
        return []

    out = []
    for v in versions_raw:
        if not isinstance(v, dict):
            continue
        out.append(Version(
            id=v.get("id", 0),
            abbr=v.get("abbreviation", ""),
            local_abbr=v.get("local_abbreviation", v.get("abbreviation", "")),
            title=v.get("title", ""),
            local_title=v.get("local_title", v.get("title", "")),
            publisher=v.get("publisher_name"),
        ))
    return out


def _find_versions(o, depth: int = 0):
    if depth > 12:
        return None
    if isinstance(o, dict):
        if "versions" in o and isinstance(o["versions"], list) and o["versions"]:
            first = o["versions"][0]
            if isinstance(first, dict) and "abbreviation" in first:
                return o["versions"]
        for v in o.values():
            r = _find_versions(v, depth + 1)
            if r is not None:
                return r
    elif isinstance(o, list):
        for it in o:
            r = _find_versions(it, depth + 1)
            if r is not None:
                return r
    return None


@dataclass
class Verse:
    chapter: int
    verse: int
    text: str


def fetch_chapter(version_id: int, book: str, chapter: int, local_abbr: str) -> list[Verse]:
    """Fetch + parse a single chapter's verses.

    Bible.com uses CSS-modules-hashed classes on the visible DOM (e.g.
    `ChapterContent-module__cat7xG__verse`). To get stable class names we read
    the canonical USFM-styled HTML from `__NEXT_DATA__.props.pageProps.chapterInfo.content`,
    which uses plain `verse vN` classes.
    """
    url = f"{BASE}/bible/{version_id}/{book}.{chapter}.{local_abbr}"
    res = scrape(url, only=["httpx", "curl_cffi"])

    # Extract chapterInfo.content from Next.js data
    m = re.search(r"__NEXT_DATA__[^>]*>(\{.+?\})</script>", res.html, re.DOTALL)
    content_html = ""
    if m:
        try:
            data = json.loads(m.group(1))
            ci = _find_key(data, "chapterInfo")
            if ci and isinstance(ci, dict):
                content_html = ci.get("content", "") or ""
        except json.JSONDecodeError:
            pass

    # Fallback: parse rendered DOM with hashed class names
    if not content_html:
        content_html = res.html

    soup = BeautifulSoup(content_html, "html.parser")

    verses: list[Verse] = []
    # Match either `verse vN` or `*__verse` with `data-usfm="BOOK.CHAP.VERSE"`
    candidates = soup.find_all("span", attrs={"data-usfm": True})
    if not candidates:
        candidates = soup.find_all(class_=re.compile(r"(?:^|_)verse(?:_|$|\s)"))

    for vs in candidates:
        # Get verse number from data-usfm or class
        usfm = vs.get("data-usfm", "")
        verse_num = None
        if usfm:
            parts = usfm.split(".")
            if len(parts) >= 3 and parts[-1].isdigit():
                verse_num = int(parts[-1])
        if verse_num is None:
            for c in vs.get("class", []):
                cm = re.match(r"v(\d+)$", c)
                if cm:
                    verse_num = int(cm.group(1))
                    break
        if verse_num is None:
            continue

        # Collect verse text from .content spans, falling back to all text minus label
        text_parts: list[str] = []
        contents = vs.find_all(class_=re.compile(r"(?:^|_)content(?:$|_)"))
        if contents:
            text_parts = [c.get_text(strip=True) for c in contents]
        if not text_parts:
            raw = vs.get_text(strip=True)
            raw = re.sub(r"^\d+", "", raw).strip()
            text_parts = [raw]

        text = " ".join(text_parts)
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            verses.append(Verse(chapter=chapter, verse=verse_num, text=text))

    # Dedupe
    seen: set[int] = set()
    deduped: list[Verse] = []
    for v in sorted(verses, key=lambda x: x.verse):
        if v.verse not in seen:
            seen.add(v.verse)
            deduped.append(v)
    return deduped


def _find_key(o, key: str, depth: int = 0):
    if depth > 14:
        return None
    if isinstance(o, dict):
        if key in o:
            return o[key]
        for v in o.values():
            r = _find_key(v, key, depth + 1)
            if r is not None:
                return r
    elif isinstance(o, list):
        for it in o:
            r = _find_key(it, key, depth + 1)
            if r is not None:
                return r
    return None


def iter_nt_chapters() -> Iterator[tuple[str, int]]:
    for book, n in NT_BOOKS:
        for ch in range(1, n + 1):
            yield (book, ch)


def fetch_nt(
    version_id: int,
    local_abbr: str,
    *,
    delay: float = DEFAULT_DELAY,
    progress_cb=None,
) -> dict[tuple[str, int], list[Verse]]:
    """Fetch all 260 NT chapters for a version. Returns dict keyed by (book, chapter)."""
    out: dict[tuple[str, int], list[Verse]] = {}
    for i, (book, ch) in enumerate(iter_nt_chapters()):
        try:
            verses = fetch_chapter(version_id, book, ch, local_abbr)
        except ScrapeError as e:
            verses = []
            if progress_cb:
                progress_cb(i, book, ch, f"FAIL: {e}")
        out[(book, ch)] = verses
        if progress_cb:
            progress_cb(i, book, ch, f"{len(verses)} verses")
        time.sleep(delay)
    return out
