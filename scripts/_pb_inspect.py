"""Inspect authenticated progress.bible data page structure."""
import re
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1] / "data" / "research" / "progress_bible"
auth_html = (ROOT / "progress_bible_products_data_.html").read_text()
soup = BeautifulSoup(auth_html, "html.parser")

print("=== title ===")
print(" ", soup.title.string if soup.title else "")

print("\n=== headings ===")
for h in soup.find_all(["h1", "h2", "h3"])[:10]:
    print(f"  {h.name}: {h.get_text(strip=True)[:100]}")

print("\n=== iframes + forms ===")
for f in soup.find_all(["iframe", "form"]):
    src = f.get("src")
    action = f.get("action")
    print(f"  {f.name}: src={src} action={action}")

print("\n=== files: png/pdf/csv/xlsx/json ===")
n = 0
for tag in soup.find_all(["a", "img"]):
    url = tag.get("src") or tag.get("href")
    if url and re.search(r"\.(png|jpg|pdf|csv|xlsx|json|zip)(\?|$)", url):
        print(f"  {tag.name}: {url[:130]}")
        n += 1
        if n >= 20:
            break

print("\n=== /products/data/<X>/ matches ===")
for m in re.finditer(r"/products/data/([^/\"\\s]+)/", auth_html):
    print(f"  {m.group(0)}")
    if len(list(re.finditer(r"/products/data/([^/\"\\s]+)/", auth_html))) > 30:
        break

print("\n=== json blobs / script data ===")
for s in soup.find_all("script"):
    txt = s.get_text()
    if "data" in txt.lower() and ("language" in txt.lower() or "country" in txt.lower()):
        snippet = txt[:500].strip()
        if snippet:
            print(f"  script: {snippet[:300]}...")
            break

print("\n=== sample raw HTML around 'data' keyword (excerpt) ===")
for m in re.finditer(r".{0,80}data[^.\\s]{0,40}", auth_html, re.I):
    s = m.group(0).strip()
    if "https" in s.lower() or "<" in s:
        continue
    if len(s) > 30:
        print(f"  ...{s[:130]}...")
        break

print("\n=== all unique progress.bible/products/* hrefs ===")
hrefs = set()
for a in soup.find_all("a", href=True):
    if "progress.bible" in a["href"]:
        hrefs.add(a["href"])
for h in sorted(hrefs):
    print(f"  {h}")
