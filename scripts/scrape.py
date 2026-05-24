"""CLI: scrape a URL with auto-fallback through Cloudflare/WAF-blocked sites.

Usage:
  python scripts/scrape.py <url>
  python scripts/scrape.py <url> --links              # print outbound URLs
  python scripts/scrape.py <url> --text               # print plain text
  python scripts/scrape.py <url> --out file.html      # save to file
  python scripts/scrape.py <url> --only curl_cffi     # restrict tier
  python scripts/scrape.py <url> --skip flaresolverr  # exclude tier
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich import print as rprint

from aiserver import scrape as S


def main(
    url: str,
    out: Path | None = typer.Option(None, "--out", "-o", help="Save HTML to file"),
    links: bool = typer.Option(False, "--links", help="Print outbound links instead of HTML"),
    text: bool = typer.Option(False, "--text", help="Print plain text instead of HTML"),
    only: str | None = typer.Option(None, "--only", help="Restrict to tier (comma-separated)"),
    skip: str | None = typer.Option(None, "--skip", help="Skip tier(s)"),
    quiet: bool = typer.Option(False, "--quiet", "-q"),
) -> None:
    only_l = only.split(",") if only else None
    skip_l = skip.split(",") if skip else None

    try:
        result = S.scrape(url, only=only_l, skip=skip_l)
    except S.ScrapeError as e:
        rprint(f"[red]FAIL:[/red] {e}")
        raise typer.Exit(1)

    if not quiet:
        rprint(
            f"[green]OK[/green] tier=[bold]{result.tier}[/bold] "
            f"status={result.status} bytes={len(result.html)} "
            f"elapsed={result.elapsed_s:.1f}s"
        )

    if links:
        urls = S.extract_links(result.html, url)
        for u in sorted(set(urls)):
            print(u)
        return

    if text:
        print(S.extract_text(result.html))
        return

    if out:
        out.write_text(result.html)
        if not quiet:
            rprint(f"[green]Wrote[/green] {out} ({out.stat().st_size} bytes)")
        return

    # Default: print HTML
    print(result.html)


if __name__ == "__main__":
    typer.run(main)
