"""Search DBP for audio Bibles in target languages. Read-only — no downloads.

Usage:
  python scripts/dbp_search.py             # all 19 target langs
  python scripts/dbp_search.py ndc chw    # specific ISOs
"""

import sys

from rich import print as rprint
from rich.table import Table

from aiserver import dbp
from aiserver.languages import LANGS


def main(isos: list[str] | None = None) -> None:
    isos = isos or list(LANGS.keys())

    t = Table(title="DBP audio Bible availability")
    t.add_column("ISO")
    t.add_column("Lang")
    t.add_column("Bible ID")
    t.add_column("Vernacular name", overflow="fold")
    t.add_column("Audio filesets", overflow="fold")
    t.add_column("Text filesets", overflow="fold")

    for iso in isos:
        lang = LANGS[iso]
        try:
            bibles = dbp.list_bibles(language_code=iso)
        except Exception as e:
            rprint(f"[red]{iso}: API error {e}[/red]")
            continue

        if not bibles:
            t.add_row(iso, lang.name, "-", "-", "[dim]no audio Bibles[/dim]", "-")
            continue

        for b in bibles:
            audio = [f for f in b.filesets if "audio" in f.set_type_code]
            text = [f for f in b.filesets if "text" in f.set_type_code]
            a_summary = ", ".join(f"{f.fileset_id}({f.set_size_code})" for f in audio) or "-"
            x_summary = ", ".join(f"{f.fileset_id}({f.set_size_code})" for f in text) or "-"
            t.add_row(iso, lang.name, b.id, b.name_vernacular or b.name_english, a_summary, x_summary)

    rprint(t)


if __name__ == "__main__":
    args = sys.argv[1:]
    main(args if args else None)
