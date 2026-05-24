"""Probe Bible.com language page for version IDs."""
import json
import re
import sys
from pathlib import Path
from bs4 import BeautifulSoup

html = Path("/tmp/bc_sna.html").read_text()

# Find Next.js data
m = re.search(r"__NEXT_DATA__[^>]*>(\{.+?\})</script>", html, re.DOTALL)
if m:
    try:
        data = json.loads(m.group(1))

        def find_versions(obj, path=""):
            if isinstance(obj, dict):
                if "versions" in obj and isinstance(obj["versions"], list):
                    print(f"Found versions at {path}: {len(obj['versions'])} items")
                    for v in obj["versions"][:10]:
                        keys = list(v.keys()) if isinstance(v, dict) else "?"
                        print(f"  {v if not isinstance(v, dict) else str(v)[:300]}")
                    return True
                for k, v in obj.items():
                    if find_versions(v, f"{path}.{k}"):
                        return True
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    if find_versions(item, f"{path}[{i}]"):
                        return True
            return False

        find_versions(data)
    except Exception as e:
        print(f"JSON parse fail: {e}")

print()
print("=== /versions/<id>-<abbr> regex matches ===")
for m in sorted(set(re.findall(r"/versions/(\d+)-([A-Z0-9-]+)", html))):
    print(f"  id={m[0]} abbr={m[1]}")

print()
print("=== /bible/<id>/<book>.<chap>.<abbr> ===")
for m in sorted(set(re.findall(r"/bible/(\d+)/[A-Z]+\.\d+\.[A-Z0-9]+", html)))[:10]:
    print(f"  {m}")
