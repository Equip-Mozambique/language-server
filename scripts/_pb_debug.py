"""Debug progress.bible login behavior."""
from bs4 import BeautifulSoup
from curl_cffi import requests as cc
import os

s = cc.Session(impersonate="chrome120")

# Check register page
r2 = s.get("https://progress.bible/register/")
print(f"GET /register/: {r2.status_code}, {len(r2.text)} bytes")
soup2 = BeautifulSoup(r2.text, "html.parser")
forms = soup2.find_all("form")
print(f"forms on register: {len(forms)}")
for form in forms:
    action = form.get("action")
    method = form.get("method")
    print(f"  action={action} method={method}")
    for inp in form.find_all(["input", "button"])[:15]:
        n = inp.get("name")
        t = inp.get("type")
        p = inp.get("placeholder", "")
        if n or p:
            print(f"    name={n} type={t} placeholder={p}")

# Now attempt login + check POST response carefully
print("\n=== POST login ===")
r3 = s.get("https://progress.bible/login/")
soup3 = BeautifulSoup(r3.text, "html.parser")
nonce_el = soup3.find("input", attrs={"name": "pp-lf-login-nonce"})
nonce = nonce_el["value"] if nonce_el else None
print(f"nonce: {nonce}")
ref_el = soup3.find("input", attrs={"name": "_wp_http_referer"})
ref = ref_el["value"] if ref_el else "/login/"

user = os.environ["PROGRESS_BIBLE_USER"]
pwd = os.environ["PROGRESS_BIBLE_PASS"]

payload = {
    "pp-lf-login-nonce": nonce,
    "_wp_http_referer": ref,
    "redirect_to": "https://progress.bible/",
    "log": user,
    "pwd": pwd,
    "rememberme": "forever",
    "wp-submit": "Log In",
}

r4 = s.post(
    "https://progress.bible/wp-login.php?wpe-login=true",
    data=payload,
    headers={"Referer": "https://progress.bible/login/"},
    timeout=30,
    allow_redirects=False,
)
print(f"POST direct: {r4.status_code}")
print(f"headers: Location={r4.headers.get('Location')}, Set-Cookie count={len(r4.headers.get_list('Set-Cookie')) if hasattr(r4.headers,'get_list') else '?'}")
print(f"body first 500: {r4.text[:500]}")

# Now allow redirects
r5 = s.post(
    "https://progress.bible/wp-login.php?wpe-login=true",
    data=payload,
    headers={"Referer": "https://progress.bible/login/"},
    timeout=30,
    allow_redirects=True,
)
print(f"\nfollowed: {r5.status_code} {r5.url}")
print(f"cookies after: {list(s.cookies.keys())}")

# Search for error markers
soup5 = BeautifulSoup(r5.text, "html.parser")
errs = soup5.find_all(class_=lambda c: c and ("error" in c.lower() or "alert" in c.lower()))
for e in errs[:5]:
    txt = e.get_text(strip=True)[:200]
    if txt:
        print(f"  err marker: {txt}")
