#!/usr/bin/env python3
"""Pull DBS catalog JSON from github.com/digitalbiblesociety/data and write
`data/research/bible_catalogs/filtered_bibles.json` filtered for target ISOs.

Run with no args:
    uv run python scripts/dbs_fetch.py

Reads target ISO codes from `aiserver.languages.LANGS`. Output is consumed by
`aiserver.resources.get_resources` to render the "DBS Bible catalog" section
of the GUI Resources tab.
"""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aiserver.languages import LANGS  # noqa: E402

OUT_DIR = ROOT / "data" / "research" / "bible_catalogs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

RAW_BASE = "https://raw.githubusercontent.com/digitalbiblesociety/data/main"

SOURCE_FILES = [
    "bibles.json",
    "bibles_dbs.json",
    "languages.json",
    "bible_audioplayers.json",
]


def fetch(name: str) -> bytes:
    url = f"{RAW_BASE}/{name}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def main() -> int:
    raw_dir = OUT_DIR / "dbs_data_repo"
    raw_dir.mkdir(parents=True, exist_ok=True)

    targets = set(LANGS)
    # Extra related ISOs surfaced in the catalog
    targets.update({"nyu", "mgh"})

    print(f"==> targets: {len(targets)} ISOs")
    for fname in SOURCE_FILES:
        dest = raw_dir / fname
        if dest.exists() and dest.stat().st_size > 100:
            print(f"  cached {fname} ({dest.stat().st_size} B)")
            continue
        print(f"  fetching {fname} ...", end=" ", flush=True)
        try:
            dest.write_bytes(fetch(fname))
            print(f"OK ({dest.stat().st_size} B)")
        except Exception as e:
            print(f"FAIL {e}")

    bibles_path = raw_dir / "bibles.json"
    if not bibles_path.exists():
        print("error: bibles.json missing, cannot filter")
        return 1

    all_bibles = json.loads(bibles_path.read_text())
    filtered = [b for b in all_bibles if isinstance(b, dict) and b.get("iso") in targets]
    print(f"==> {len(filtered)} bibles match target ISOs")

    out = OUT_DIR / "filtered_bibles.json"
    out.write_text(json.dumps(filtered, ensure_ascii=False, indent=2))
    print(f"==> wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
