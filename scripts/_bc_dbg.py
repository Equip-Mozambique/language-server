import re
import json
from bs4 import BeautifulSoup

raw = open("/tmp/bc_ndc.html").read()
s = BeautifulSoup(raw, "html.parser")
verses = s.find_all(class_=re.compile(r"verse"))
print(f"verse-class elements: {len(verses)}")
if verses:
    v = verses[0]
    print(f"  classes: {v.get('class')}")
    print(f"  html: {str(v)[:300]}")
ci = s.find(class_=re.compile(r"ChapterContent|chapter-content"))
if ci:
    print(f"chapter content class: {ci.get('class')}")
    print(f"  text excerpt: {ci.get_text()[:300]}")

m = re.search(r"__NEXT_DATA__[^>]*>(\{.+?\})</script>", raw, re.DOTALL)
if m:
    d = json.loads(m.group(1))

    def find(o, target_key, depth=0):
        if depth > 12: return None
        if isinstance(o, dict):
            if target_key in o:
                return o[target_key]
            for v in o.values():
                r = find(v, target_key, depth+1)
                if r is not None: return r
        elif isinstance(o, list):
            for it in o:
                r = find(it, target_key, depth+1)
                if r is not None: return r
        return None

    ci_data = find(d, "chapterInfo")
    if ci_data and isinstance(ci_data, dict):
        print(f"\nchapterInfo keys: {list(ci_data.keys())}")
        content = ci_data.get("content", "")
        print(f"content len: {len(content)}")
        print(f"content excerpt: {content[:600]}")
