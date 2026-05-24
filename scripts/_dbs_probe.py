"""Find DBS audio URL pattern by inspecting the listener page."""
from bs4 import BeautifulSoup
from pathlib import Path

html = open("/tmp/dbs_listen.html").read()
s = BeautifulSoup(html, "html.parser")

print("=== external scripts ===")
for sc in s.find_all("script", src=True):
    src = sc.get("src", "")
    if src and not src.startswith("data:"):
        print(f"  {src}")

print("\n=== inline scripts mentioning audio/mp3/davar/fcbh ===")
for sc in s.find_all("script"):
    txt = sc.string or ""
    if any(k in txt.lower() for k in ["audio.dbs", "mp3", "davar", "fcbh", "fileset", "apiurl", "audio:"]):
        print(f"--- snippet (first 600) ---")
        print(txt[:600])
        print()

print("\n=== iframes ===")
for f in s.find_all("iframe"):
    print(f"  src: {f.get('src')}")

# Look for any url patterns in the raw HTML
import re
print("\n=== url-like strings with /audio/ or audio.dbs.org ===")
for m in re.finditer(r"https?://[a-zA-Z0-9.-]+/[^\s\"'<>]*", html):
    u = m.group(0)
    if "audio" in u.lower() or "dbs" in u.lower():
        print(f"  {u[:140]}")
