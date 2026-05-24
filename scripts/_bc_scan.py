"""Quick scan of Bible.com version counts per target ISO."""
from aiserver import biblecom
from aiserver.languages import LANGS

print(f"{'iso':<5} {'lang':<22} {'#versions'}")
print("-" * 50)
for iso, lang in LANGS.items():
    try:
        vs = biblecom.list_versions(iso)
        count = len(vs)
        sample = ""
        if vs:
            v = vs[0]
            sample = f"{v.local_abbr} ({v.publisher or '?'})"
    except Exception as e:
        print(f"{iso:<5} {lang.name:<22} ERROR: {e}")
        continue
    print(f"{iso:<5} {lang.name:<22} {count:<3} {sample[:60]}")
