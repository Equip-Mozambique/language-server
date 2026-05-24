"""Discover Arclight (Jesus Film) video coverage for our 19 target ISOs.

For each ISO, search by language name, fetch component list, dump JSON inventory.
"""

from __future__ import annotations

import json
from pathlib import Path

from rich import print as rprint
from rich.table import Table

from aiserver import arclight
from aiserver.languages import LANGS


OUT_DIR = Path(__file__).resolve().parents[1] / "data" / "research" / "arclight"

# Search terms: use English name + native name + ISO since Arclight indexes by name not ISO
SEARCH_OVERRIDES = {
    "ndc": "Ndau",
    "nya": "Chichewa",
    "tso": "Tsonga",
    "ven": "Venda",
    "vmw": "Makhuwa",
    "seh": "Sena",
    "ngl": "Lomwe",
    "chw": "Chuwabo",
    "tsc": "Tswa",
    "rng": "Ronga",
    "yao": "Yao",
    "kde": "Makonde",
    "kck": "Kalanga",
    "nmq": "Nambya",
    "nde": "Ndebele",
    "nbl": "Ndebele",
    "toi": "Tonga",
    "sna": "Shona",
    "por": "Portuguese",
    "mgh": "Makhuwa",
}


def discover_for_iso(iso: str) -> dict:
    """Find languageId(s) for an ISO and list their components."""
    name = SEARCH_OVERRIDES.get(iso, LANGS[iso].name if iso in LANGS else iso)
    rprint(f"\n[cyan]{iso}[/cyan] ({name}):")
    try:
        langs = arclight.search_languages(name)
    except Exception as e:
        rprint(f"  [red]search FAIL: {e}[/red]")
        return {"iso": iso, "error": str(e)}

    # Filter to matching iso639_3 (case insensitive); fall back to all results
    matching = [l for l in langs if l.iso639_3.lower() == iso.lower()]
    if not matching:
        matching = langs  # take whatever the search returned

    rprint(f"  Arclight languages: {len(matching)}")

    result = {"iso": iso, "name": name, "languages": []}
    for l in matching:
        rprint(f"  - id={l.language_id} iso={l.iso639_3} {l.name}")
        try:
            comps = arclight.list_components(l.language_id)
        except Exception as e:
            comps = []
            rprint(f"    [yellow]list_components FAIL: {e}[/yellow]")

        feats = [c for c in comps if c.sub_type == "featureFilm"]
        shorts = [c for c in comps if c.sub_type == "shortFilm"]
        series = [c for c in comps if c.sub_type == "series"]

        # Highlight known films
        well_known = []
        for c in comps:
            cid = c.component_id
            if cid in ("1_jf-0-0", "1_mld-0-0", "1_cl-0-0"):
                well_known.append((cid, c.title, c.length_ms))

        result["languages"].append({
            "language_id": l.language_id,
            "name": l.name,
            "iso": l.iso639_3,
            "feature_count": len(feats),
            "short_count": len(shorts),
            "series_count": len(series),
            "total_components": len(comps),
            "well_known_films": well_known,
            "components": [
                {
                    "id": c.component_id,
                    "type": c.sub_type,
                    "title": c.title,
                    "length_s": c.length_ms / 1000,
                    "downloadable": c.is_downloadable,
                }
                for c in comps
            ],
        })
    return result


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    summary = []
    for iso in LANGS:
        data = discover_for_iso(iso)
        (OUT_DIR / f"{iso}.json").write_text(json.dumps(data, indent=2, ensure_ascii=False))

        # Best-language summary row
        if data.get("languages"):
            best = max(data["languages"], key=lambda x: x["feature_count"])
            summary.append({
                "iso": iso,
                "language_id": best["language_id"],
                "name": best["name"],
                "features": best["feature_count"],
                "shorts": best["short_count"],
                "series": best["series_count"],
                "has_jf": any(w[0] == "1_jf-0-0" for w in best.get("well_known_films", [])),
                "has_mag": any(w[0] == "1_mld-0-0" for w in best.get("well_known_films", [])),
                "has_sojc": any(w[0] == "1_cl-0-0" for w in best.get("well_known_films", [])),
            })

    # Table summary
    t = Table(title=f"Arclight coverage — {len(summary)} target ISOs")
    t.add_column("ISO")
    t.add_column("LangID")
    t.add_column("Name")
    t.add_column("Feat")
    t.add_column("Short")
    t.add_column("Series")
    t.add_column("JF")
    t.add_column("Mag")
    t.add_column("SoJC")
    for s in summary:
        t.add_row(
            s["iso"], str(s["language_id"]), s["name"][:25],
            str(s["features"]), str(s["shorts"]), str(s["series"]),
            "✓" if s["has_jf"] else "—",
            "✓" if s["has_mag"] else "—",
            "✓" if s["has_sojc"] else "—",
        )
    rprint(t)

    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
