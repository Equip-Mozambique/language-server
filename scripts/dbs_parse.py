"""Parse DBS audio catalog JSON, summarize target-lang coverage."""

import json
import sys
from pathlib import Path

import httpx

DATA_OUT = Path(__file__).resolve().parents[1] / "data" / "research" / "dbs"

TARGETS = {
    "sna": "Shona", "nde": "Ndebele (N.)", "nbl": "Ndebele (S.)",
    "nya": "Chichewa/Nyanja", "toi": "Tonga", "kck": "Kalanga", "nmq": "Nambya",
    "ven": "Venda", "tso": "Tsonga", "por": "Portuguese", "vmw": "Makhuwa",
    "seh": "Sena", "ngl": "Lomwe", "chw": "Chuwabo", "ndc": "Ndau",
    "tsc": "Tswa", "rng": "Ronga", "yao": "Yao",
}


def main() -> None:
    catalog_path = DATA_OUT / "index.json"
    if not catalog_path.exists() or "--refetch" in sys.argv:
        DATA_OUT.mkdir(parents=True, exist_ok=True)
        print("Fetching catalog...")
        # Use scrape module for safety
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
        from aiserver.scrape import scrape
        r = scrape("https://audio.dbs.org/index.json")
        catalog_path.write_text(r.html)

    data = json.loads(catalog_path.read_text())
    print(f"Total catalog entries: {len(data)}")
    isos = sorted({d.get("iso", "") for d in data if d.get("iso")})
    print(f"Unique ISOs: {len(isos)}")
    scopes = sorted({d.get("scope", "") for d in data})
    print(f"Scopes: {scopes}")
    print()

    print("=== TARGET LANGUAGE COVERAGE ===")
    hits_by_target = {}
    for iso, name in TARGETS.items():
        hits = [d for d in data if d.get("iso") == iso]
        hits_by_target[iso] = hits
        if hits:
            print(f"\n{iso} ({name}): {len(hits)} entry(s)")
            for h in hits:
                tt = (h.get("tt") or "")[:50]
                tv = (h.get("tv") or "")[:40]
                pub = (h.get("pb") or "")[:40]
                print(f"  {h.get('abbr'):<10} | {h.get('cn'):<15} | scope={h.get('scope'):<12} | {tt} | {tv} | {pub}")
        else:
            print(f"\n{iso} ({name}): NONE")

    out_path = DATA_OUT / "target_coverage.json"
    out_path.write_text(json.dumps(hits_by_target, indent=2, ensure_ascii=False))
    print(f"\nSaved -> {out_path}")

    # Adjacent / related lang scan (Bantu)
    bantu_isos = {"swh","kde","kuj","suk","run","sna","chw","mgh","mhh","wmw","nyu","mwm","cce","kde","mwn","jmc","gum","kdc","nyf","kik","kam","luo","gax"}
    bantu_in_dbs = sorted(set(isos) & bantu_isos)
    print(f"\n=== Bantu / E.African adjacent ISOs in catalog: {len(bantu_in_dbs)} ===")
    for iso in bantu_in_dbs:
        hits = [d for d in data if d.get("iso") == iso]
        if hits:
            h = hits[0]
            print(f"  {iso} ({h.get('ln')}): {len(hits)} bibles | first: {h.get('abbr')} {h.get('cn')}")


if __name__ == "__main__":
    main()
