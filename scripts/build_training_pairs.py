"""Join DBP audio manifests + Bible.com text manifests → training pairs.

Per ISO with both audio (data/audio/<iso>/<fileset>/manifest.json) and text
(data/text/<iso>/<abbr>/nt_manifest.json) present, emit a JSONL of chapter-level
(audio, transcript) pairs.

Output: data/pairs/<iso>/pairs.jsonl
Each line: {
  "iso": "sna",
  "audio_path": "/absolute/path/to/MAT_001.mp3",
  "audio_relpath": "sna/SNABSZN2DA/MAT_001.mp3",
  "duration_s": 247,
  "book": "MAT",
  "chapter": 1,
  "text": "concatenated chapter text",
  "verses": [{"verse": 1, "text": "..."}, ...],
  "text_version_id": 1931,
  "text_version_abbr": "SUB1949",
  "audio_fileset": "SNABSZN2DA"
}
"""

from __future__ import annotations

import json
from pathlib import Path

from rich import print as rprint
from rich.table import Table


DATA_ROOT = Path(__file__).resolve().parents[1] / "data"
PAIRS_ROOT = DATA_ROOT / "pairs"


def find_audio_manifests(iso: str) -> list[Path]:
    iso_dir = DATA_ROOT / "audio" / iso
    if not iso_dir.exists():
        return []
    out: list[Path] = []
    for sub in iso_dir.iterdir():
        if sub.is_dir():
            m = sub / "manifest.json"
            if m.exists():
                out.append(m)
    return out


def find_text_manifests(iso: str) -> list[Path]:
    iso_dir = DATA_ROOT / "text" / iso
    if not iso_dir.exists():
        return []
    out: list[Path] = []
    for sub in iso_dir.iterdir():
        if sub.is_dir():
            m = sub / "nt_manifest.json"
            if m.exists():
                out.append(m)
    return out


def build_pairs(iso: str) -> tuple[int, int, Path | None]:
    """Build training pairs for one ISO. Returns (n_pairs, n_with_text, output_path)."""
    audio_manifests = find_audio_manifests(iso)
    text_manifests = find_text_manifests(iso)

    if not audio_manifests:
        rprint(f"  [yellow]{iso}: no audio[/yellow]")
        return 0, 0, None
    if not text_manifests:
        rprint(f"  [yellow]{iso}: no text[/yellow]")
        return 0, 0, None

    # Use the first audio fileset (DBP NT) + first text version
    audio_manifest_path = audio_manifests[0]
    text_manifest_path = text_manifests[0]

    audio_manifest = json.loads(audio_manifest_path.read_text())
    text_manifest = json.loads(text_manifest_path.read_text())

    fileset = audio_manifest_path.parent.name
    text_version = text_manifest_path.parent.name
    audio_dir = audio_manifest_path.parent

    text_chapters: dict[str, list[dict]] = text_manifest.get("chapters", {})

    pairs: list[dict] = []
    n_with_text = 0
    for entry in audio_manifest:
        book = entry.get("book")
        chapter = entry.get("chapter")
        if book is None or chapter is None:
            continue
        key = f"{book}_{int(chapter):03d}"
        verses = text_chapters.get(key, [])
        text = " ".join(v["text"] for v in verses)
        if verses:
            n_with_text += 1
        audio_relpath = f"{iso}/{fileset}/{entry['file']}"
        audio_abs = audio_dir / entry["file"]
        pairs.append({
            "iso": iso,
            "audio_path": str(audio_abs),
            "audio_relpath": audio_relpath,
            "duration_s": entry.get("duration_s"),
            "book": book,
            "chapter": int(chapter),
            "text": text,
            "verses": verses,
            "text_version_id": text_manifest.get("version_id"),
            "text_version_abbr": text_manifest.get("local_abbr") or text_version,
            "audio_fileset": fileset,
        })

    out_dir = PAIRS_ROOT / iso
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "pairs.jsonl"
    with out_path.open("w", encoding="utf-8") as f:
        for p in pairs:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    return len(pairs), n_with_text, out_path


def main() -> None:
    PAIRS_ROOT.mkdir(parents=True, exist_ok=True)
    rows: list[tuple[str, int, int, str, str]] = []
    isos = sorted({p.name for p in (DATA_ROOT / "audio").iterdir() if p.is_dir()} |
                  {p.name for p in (DATA_ROOT / "text").iterdir() if p.is_dir()})

    for iso in sorted(isos):
        if not iso or iso in ("storyrunners_manifest.json",):
            continue
        rprint(f"\n[cyan]>>> {iso}[/cyan]")
        try:
            n_pairs, n_text, out = build_pairs(iso)
        except Exception as e:
            rprint(f"  [red]FAIL: {e}[/red]")
            continue
        if n_pairs:
            cov = f"{n_text}/{n_pairs}" if n_pairs else "0/0"
            rprint(f"  [green]wrote {out}[/green] — {n_pairs} chapters, {n_text} with text ({100*n_text/max(1,n_pairs):.0f}%)")
            rows.append((iso, n_pairs, n_text, str(out), cov))

    t = Table(title=f"Training pairs — {len(rows)} ISOs")
    t.add_column("ISO")
    t.add_column("Chapters")
    t.add_column("With text")
    t.add_column("Coverage")
    t.add_column("Output")
    for iso, n_pairs, n_text, out, cov in rows:
        t.add_row(iso, str(n_pairs), str(n_text), cov, out.replace("/home/audioai/ai-server/", ""))
    rprint(t)


if __name__ == "__main__":
    main()
