"""Probe Bible.com chapter page for text content structure."""
import json
import re
from pathlib import Path
from bs4 import BeautifulSoup

html = Path("/tmp/bc_chap.html").read_text()
soup = BeautifulSoup(html, "html.parser")

# Look for verse content classes
candidates = ["verse", "ChapterContent", "chapter-content", "p", "v"]
for cls in candidates:
    els = soup.find_all(class_=re.compile(cls, re.I))
    if 1 < len(els) < 50:
        sample = els[0].get_text(strip=True)[:200]
        print(f"  class~={cls}: {len(els)} matches; sample: {sample!r}")

# Look for __NEXT_DATA__
m = re.search(r"__NEXT_DATA__[^>]*>(\{.+?\})</script>", html, re.DOTALL)
if m:
    try:
        d = json.loads(m.group(1))

        def hunt(o, p=""):
            if isinstance(o, dict):
                if "content" in o and isinstance(o["content"], str) and len(o["content"]) > 500:
                    print(f"\n  CONTENT at {p} ({len(o['content'])} chars):")
                    print("   ", o["content"][:400])
                    return True
                if "verses" in o and isinstance(o["verses"], list):
                    print(f"\n  VERSES at {p}: {len(o['verses'])} items, sample: {o['verses'][:2]}")
                    return True
                for k, v in o.items():
                    if hunt(v, f"{p}.{k}"):
                        return True
            elif isinstance(o, list):
                for i, it in enumerate(o):
                    if hunt(it, f"{p}[{i}]"):
                        return True
            return False

        hunt(d)
    except Exception as e:
        print(f"json fail: {e}")

# Plain text extraction of body
body = soup.find("body")
if body:
    text = body.get_text(separator=" ", strip=True)
    print(f"\n=== body text excerpt (around Matthew 1) ===")
    idx = text.find("Mateo") if "Mateo" in text else text.find("Mateu") if "Mateu" in text else text.find("Mateu")
    if idx < 0:
        idx = text.find("1")
    print(text[max(0, idx-50):idx+500])
