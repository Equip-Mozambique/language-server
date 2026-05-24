"""Inspect the search form on progress.bible/products/data/ + test a query."""
import os
import re
from pathlib import Path
from bs4 import BeautifulSoup
from curl_cffi import requests as cc

ROOT = Path(__file__).resolve().parents[1] / "data" / "research" / "progress_bible"

s = cc.Session(impersonate="chrome120")
s.cookies.set(
    os.environ["PB_WP_COOKIE_NAME"],
    os.environ["PB_WP_COOKIE_VALUE"],
    domain="progress.bible", path="/",
)
if cf := os.environ.get("PB_CF_CLEARANCE"):
    s.cookies.set("cf_clearance", cf, domain="progress.bible", path="/")

# Inspect the actual form
html = (ROOT / "progress_bible_products_data_.html").read_text()
soup = BeautifulSoup(html, "html.parser")
for form in soup.find_all("form"):
    action = form.get("action", "")
    if "/products/data" in action:
        print(f"FORM action={action} method={form.get('method')}")
        for el in form.find_all(["input", "select", "button", "textarea"]):
            name = el.get("name")
            etype = el.get("type", el.name)
            placeholder = el.get("placeholder", "")
            value = el.get("value", "")
            print(f"  {etype:<12} name={name!r:<25} value={value[:30]!r} placeholder={placeholder!r}")
            if etype == "select" or el.name == "select":
                for opt in el.find_all("option")[:10]:
                    print(f"     option: value={opt.get('value')!r} text={opt.get_text(strip=True)[:50]!r}")

# Now try a GET on /products/data/ with various query params to see what works
print("\n=== Try GET /products/data/?<various queries> ===")
for q in [
    "?lang=Shona",
    "?language=Shona",
    "?iso=sna",
    "?country=Zimbabwe",
    "?search=Shona",
    "?s=Shona",
]:
    url = f"https://progress.bible/products/data/{q}"
    r = s.get(url, timeout=30, headers={"Referer": "https://progress.bible/products/data/"})
    # Look for differences
    body_pngs = re.findall(r'src="([^"]*\.png)"', r.text)
    data_pngs = [p for p in body_pngs if "/products/data/" in p or re.search(r"/[A-Z]{2,3}/[A-Z0-9]{6,15}/", p)]
    print(f"  {q}: {r.status_code} bytes={len(r.text)} data-pngs={len(data_pngs)}")
    for p in data_pngs[:3]:
        print(f"     -> {p[:120]}")

# Also try POST
print("\n=== Try POST with form data ===")
payload_attempts = [
    {"language": "Shona"},
    {"lang": "Shona"},
    {"search": "Shona"},
    {"q": "Shona"},
]
for payload in payload_attempts:
    r = s.post("https://progress.bible/products/data/", data=payload, timeout=30, headers={"Referer": "https://progress.bible/products/data/"})
    body_pngs = re.findall(r'src="([^"]*\.png)"', r.text)
    data_pngs = [p for p in body_pngs if re.search(r"/[A-Z]{2,3}/[A-Z0-9]{6,15}/", p)]
    print(f"  POST {payload}: {r.status_code} bytes={len(r.text)} data-pngs={len(data_pngs)}")
    for p in data_pngs[:3]:
        print(f"     -> {p[:120]}")
