"""Download StoryRunners Bible storyset zips for target languages.

StoryRunners (Cru) publishes oral Bible storysets — clean MP3 narration of
"The Promise" (Creation → Christ's return). Non-commercial research OK.

Source page: https://www.storyrunners.org/stories-v2/
S3 host:     https://storysets.s3.amazonaws.com/<code>/<Name>_Storyset.zip
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import httpx
from rich import print as rprint
from rich.progress import Progress

DATA_ROOT = Path(__file__).resolve().parents[1] / "data" / "audio"

# Verified 2026-05-24. Map ISO → (StoryRunners code, zip URL).
# Note: storyrunners "Shona Southeast" (likely ndc/Ndau) and "Shona Central"
# (sna) point to the same S3 zip — only one Shona set exists. Stored under sna.
TARGETS = {
    # Primary target langs
    "sna": ("https://storysets.s3.amazonaws.com/sna/Shona_Storyset.zip", "Shona-Central"),
    "nde": ("https://storysets.s3.us-east-1.amazonaws.com/nde/Ndebele_Zimbabwe_Storyset.zip", "Ndebele-Zimbabwe"),
    "nya": ("https://storysets.s3.amazonaws.com/nya/Chichewa_Malawi_Storyset.zip", "Chichewa-Malawi"),
    "tso": ("https://storysets.s3.amazonaws.com/tso/Shangaan_Storyset.zip", "Shangaan"),
    "yao": ("https://storysets.s3.amazonaws.com/yao/Yao_Malawi_Storyset.zip", "Yao-Malawi"),
    # Cross-lingual transfer (Bantu / nearby + English anchor for parallel alignment)
    "kde": ("https://storysets.s3.amazonaws.com/kde/Makonde_Storyset.zip", "Makonde"),       # N. Mozambique
    "swh": ("https://storysets.s3.amazonaws.com/swh/Swahili_Storyset.zip", "Swahili"),       # Bantu base
    "kuj": ("https://storysets.s3.amazonaws.com/kuj/Kuria_Tanzania.zip", "Kuria-Tanzania"),
    "suk": ("https://storysets.s3.amazonaws.com/suk/Sukuma_Storyset.zip", "Sukuma"),
    "rim": ("https://storysets.s3.amazonaws.com/rim/Nyaturu_Storyset.zip", "Nyaturu"),
    "run": ("https://storysets.s3.amazonaws.com/run/Rundi_Burundi_Storyset.zip", "Rundi-Burundi"),
    "mas": ("https://storysets.s3.amazonaws.com/mas/Maasai_Storyset.zip", "Maasai"),         # Nilotic, less close
    "eng": ("https://storysets.s3.amazonaws.com/eng/English_Storyset.zip", "English"),       # Parallel anchor
}


def download(url: str, dest: Path) -> int:
    dest.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with httpx.stream("GET", url, timeout=120.0, follow_redirects=True) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length") or 0)
        with dest.open("wb") as f, Progress() as prog:
            task = prog.add_task(dest.name, total=total or None)
            for chunk in r.iter_bytes(1 << 16):
                f.write(chunk)
                written += len(chunk)
                prog.update(task, completed=written)
    return written


def main() -> None:
    for iso, (url, label) in TARGETS.items():
        out_dir = DATA_ROOT / iso / "storyrunners"
        out_dir.mkdir(parents=True, exist_ok=True)
        zip_path = out_dir / f"{label}_Storyset.zip"

        if zip_path.exists():
            rprint(f"[dim]{iso}: zip exists ({zip_path.stat().st_size//1024}K) — skipping download[/dim]")
        else:
            rprint(f"[cyan]{iso}:[/cyan] downloading {url}")
            try:
                size = download(url, zip_path)
                rprint(f"  -> {size//1024}K written")
            except Exception as e:
                rprint(f"  [red]FAIL: {e}[/red]")
                continue

        # Unzip
        extract_dir = out_dir / "extracted"
        if not extract_dir.exists():
            rprint(f"  unzipping...")
            with zipfile.ZipFile(zip_path) as zf:
                zf.extractall(extract_dir)
            # Inventory
            mp3s = sorted(extract_dir.rglob("*.mp3"))
            wavs = sorted(extract_dir.rglob("*.wav"))
            pdfs = sorted(extract_dir.rglob("*.pdf"))
            txts = sorted(extract_dir.rglob("*.txt"))
            rprint(f"  extracted: {len(mp3s)} mp3, {len(wavs)} wav, {len(pdfs)} pdf, {len(txts)} txt")
        else:
            rprint(f"  [dim]already extracted[/dim]")


if __name__ == "__main__":
    main()
