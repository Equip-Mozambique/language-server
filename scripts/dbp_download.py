"""Download an entire DBP audio fileset for a language → local mp3 + manifest.

Pulls audio chapter-by-chapter and writes a manifest JSON pairing each audio
file with its book/chapter/verse text from a sibling text fileset (when one
exists in the same language).

Usage:
  python scripts/dbp_download.py <iso> [--audio-fileset ID] [--text-fileset ID]
  python scripts/dbp_download.py ndc                # auto-pick best filesets
  python scripts/dbp_download.py ven --audio-fileset VEN98DA --text-fileset VEN98WBT
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import typer
from rich import print as rprint
from rich.progress import Progress

from aiserver import dbp
from aiserver.languages import LANGS

DATA_ROOT = Path(__file__).resolve().parents[1] / "data" / "audio"


def pick_best_filesets(iso: str) -> tuple[dbp.Fileset | None, dbp.Fileset | None, dbp.Bible | None]:
    """Heuristic: prefer audio_drama > audio, full > NT > portions. Match text fileset by bible_id."""
    bibles = dbp.list_bibles(language_code=iso)
    if not bibles:
        return None, None, None

    def score_audio(f: dbp.Fileset) -> tuple[int, int, int]:
        type_rank = {"audio_drama": 2, "audio": 1}.get(f.set_type_code, 0)
        size_rank = {"C": 4, "NTOTP": 3, "NT": 2, "OT": 2, "P": 1}.get(f.set_size_code, 0)
        codec_rank = {"mp3": 2, "opus": 1}.get((f.codec or "").lower(), 0)
        return (size_rank, type_rank, codec_rank)

    def score_text(f: dbp.Fileset) -> int:
        return {"text_plain": 2, "text_usx": 1, "text_html": 1}.get(f.set_type_code, 0)

    best_bible = None
    best_audio = None
    best_text = None
    best_audio_score = (-1, -1)
    for b in bibles:
        a = [f for f in b.filesets if "audio" in f.set_type_code]
        if not a:
            continue
        a_top = max(a, key=score_audio)
        if score_audio(a_top) > best_audio_score:
            best_audio_score = score_audio(a_top)
            best_audio = a_top
            best_bible = b
            t = [f for f in b.filesets if "text" in f.set_type_code]
            best_text = max(t, key=score_text) if t else None

    return best_audio, best_text, best_bible


def download(iso: str, audio_id: str | None, text_id: str | None) -> None:
    if iso not in LANGS:
        rprint(f"[red]Unknown ISO: {iso}[/red]")
        sys.exit(1)

    if audio_id is None:
        audio_fs, text_fs, bible = pick_best_filesets(iso)
        if audio_fs is None:
            rprint(f"[red]No audio Bibles found in DBP for {iso}[/red]")
            sys.exit(1)
        audio_id = audio_fs.fileset_id
        text_id = text_id or (text_fs.fileset_id if text_fs else None)
        audio_asset = audio_fs.asset_id
        text_asset = text_fs.asset_id if text_fs else None
        rprint(f"[cyan]Auto-picked:[/cyan] bible={bible.id} audio={audio_id} text={text_id}")
    else:
        audio_asset = text_asset = None

    out_dir = DATA_ROOT / iso / audio_id
    out_dir.mkdir(parents=True, exist_ok=True)
    rprint(f"[cyan]Writing to:[/cyan] {out_dir}")

    chapters = dbp.fileset_chapters(audio_id, audio_asset)
    rprint(f"[cyan]Audio chapters:[/cyan] {len(chapters)}")

    # Determine file extension from fileset codec (mp3 > opus → .webm)
    codec = None
    if audio_id.endswith("-opus16"):
        codec, ext = "opus", "webm"
    else:
        codec, ext = "mp3", "mp3"
    rprint(f"[cyan]Codec:[/cyan] {codec} -> .{ext}")

    text_index: dict[tuple[str, int], str] = {}
    if text_id:
        verses = dbp.fileset_chapters(text_id, text_asset)
        for v in verses:
            key = (v.get("book_id", ""), int(v.get("chapter", 0) or 0))
            text_index.setdefault(key, "")
            text_index[key] += " " + (v.get("verse_text") or "").strip()
        rprint(f"[cyan]Text verses:[/cyan] {len(verses)} → {len(text_index)} chapter blocks")

    manifest = []
    with Progress() as prog:
        task = prog.add_task("download", total=len(chapters))
        for ch in chapters:
            book = ch.get("book_id") or ch.get("book")
            chapter = int(ch.get("chapter_start") or ch.get("chapter") or 0)
            url = ch.get("path") or ch.get("file_name") or ch.get("filename")
            if not url:
                prog.advance(task)
                continue
            if not url.startswith("http"):
                # path returned relative — DBP expects asset-host prefix
                files = dbp.chapter_files(audio_id, book, chapter, audio_asset)
                url = files[0].get("path") if files else None
                if not url:
                    prog.advance(task)
                    continue

            fname = f"{book}_{chapter:03d}.{ext}"
            dest = out_dir / fname
            if not dest.exists():
                try:
                    dbp.download_file(url, dest)
                except Exception as e:
                    rprint(f"[red]Failed {book} {chapter}: {e}[/red]")
                    prog.advance(task)
                    continue

            manifest.append({
                "file": fname,
                "book": book,
                "chapter": chapter,
                "text": text_index.get((book, chapter), "").strip(),
                "duration_s": ch.get("duration"),
                "verse_start": ch.get("verse_start"),
                "verse_end": ch.get("verse_end"),
            })
            prog.advance(task)

    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    rprint(f"[green]Done.[/green] {len(manifest)} chapters → {out_dir / 'manifest.json'}")


def cli(
    iso: str,
    audio_fileset: str | None = typer.Option(None, "--audio-fileset"),
    text_fileset: str | None = typer.Option(None, "--text-fileset"),
) -> None:
    download(iso, audio_fileset, text_fileset)


if __name__ == "__main__":
    typer.run(cli)
