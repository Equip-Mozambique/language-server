"""Build a parallel manifest from StoryRunners downloads.

Filename patterns observed (2026-05-24):
- `Shona-01-Creation_of_the_World.mp3`           (English title only)
- `Chichewa-01-Chiyambi-Creation.mp3`            (vernacular + English subtitle)
- `Ndebele-0.1-indlela_...-How_to_Lead_...mp3`   (instructional prefix 0.N)
- `Yao-01-Chilengedwe-Creation.mp3`

Strategy: group by integer **story number only** (ignore 0.N instructionals).
Use English-set titles as canonical labels.
"""

from __future__ import annotations

import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path

from rich import print as rprint
from rich.table import Table

DATA_ROOT = Path(__file__).resolve().parents[1] / "data" / "audio"
OUT = DATA_ROOT / "storyrunners_manifest.json"

# `<LangLabel>-<NN>(.<M>)?-<rest>.mp3` — capture only integer story number
PAT = re.compile(r"^(?P<lang>[^-]+(?:-[^-]+)?)-(?P<num>\d{1,3})(?:\.\d+)?-(?P<rest>.+)\.mp3$")
INSTRUCTIONAL = re.compile(r"-(?:0\.\d+)-")  # filename has "0.1" or "0.2" between dashes


def english_title_from_rest(rest: str) -> str:
    """Pull the trailing English subtitle from a filename's 'rest' part.

    If rest contains exactly one dash-separated chunk → assume English title only.
    If rest contains two chunks (vernacular-english) → use last chunk.
    """
    parts = rest.split("-")
    last = parts[-1].replace("_", " ").strip()
    return last


def ffprobe_duration(path: Path) -> float | None:
    try:
        r = subprocess.run(
            ["ffprobe", "-hide_banner", "-v", "error", "-show_entries",
             "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True, timeout=10,
        )
        return float(r.stdout.strip())
    except Exception:
        return None


def main() -> None:
    by_num: dict[int, dict] = defaultdict(lambda: {
        "story_num": 0,
        "english_title": "",
        "langs": {},
    })

    eng_titles: dict[int, str] = {}

    for iso_dir in sorted(DATA_ROOT.iterdir()):
        sr_dir = iso_dir / "storyrunners" / "extracted"
        if not sr_dir.exists():
            continue
        iso = iso_dir.name

        for mp3 in sr_dir.rglob("*.mp3"):
            if "__MACOSX" in str(mp3):
                continue
            # Skip instructional 0.N files
            if INSTRUCTIONAL.search(mp3.name):
                continue
            m = PAT.match(mp3.name)
            if not m:
                continue
            num = int(m.group("num"))
            title = english_title_from_rest(m.group("rest"))

            if iso == "eng":
                eng_titles[num] = title

            duration = ffprobe_duration(mp3)
            by_num[num]["story_num"] = num
            by_num[num]["langs"][iso] = {
                "file": str(mp3.relative_to(DATA_ROOT)),
                "duration_s": duration,
                "filename_title": title,
            }

    # Fill canonical English title; fall back to any lang's English subtitle
    for num, story in by_num.items():
        story["english_title"] = eng_titles.get(
            num,
            next((d["filename_title"] for d in story["langs"].values() if d.get("filename_title")), ""),
        )

    sorted_stories = dict(sorted(by_num.items()))
    OUT.write_text(json.dumps(sorted_stories, indent=2, ensure_ascii=False))
    rprint(f"[green]Wrote {OUT}[/green] ({len(sorted_stories)} stories)")

    # Coverage table
    all_langs = sorted({lang for s in sorted_stories.values() for lang in s["langs"]})
    rprint(f"[cyan]Langs:[/cyan] {', '.join(all_langs)}")

    t = Table(title=f"StoryRunners parallel coverage — {len(sorted_stories)} stories × {len(all_langs)} langs")
    t.add_column("#", style="bold")
    t.add_column("Title (EN)", overflow="fold", max_width=35)
    for lang in all_langs:
        t.add_column(lang)
    for num, data in sorted_stories.items():
        row = [str(num), data["english_title"][:33]]
        for lang in all_langs:
            row.append("✓" if lang in data["langs"] else "—")
        t.add_row(*row)
    rprint(t)

    # Summary stats
    counts = defaultdict(int)
    total_dur = defaultdict(float)
    for data in sorted_stories.values():
        for lang, info in data["langs"].items():
            counts[lang] += 1
            total_dur[lang] += info.get("duration_s") or 0.0

    rprint("\n[bold]Per-language story count + total duration:[/bold]")
    for lang in all_langs:
        h = total_dur[lang] / 3600
        rprint(f"  {lang}: {counts[lang]} stories, {h:.1f}h")


if __name__ == "__main__":
    main()
