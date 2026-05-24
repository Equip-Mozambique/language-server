"""Crawl previously-blocked sites for outbound links + DBS catalog.

Now that `aiserver.scrape` unlocks Cloudflare/WAF blocks, re-do the link-discovery
crawl on the 8 sites that earlier 403'd.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse

from rich import print as rprint

from aiserver.scrape import scrape, extract_links, ScrapeError


# Sites previously-blocked, now scrapable + their priority pages
TARGETS = {
    "dbs.org": [
        "https://dbs.org",
        "https://dbs.org/en/bibles",
        "https://dbs.org/audio",
        "https://dbs.org/about/partners",
    ],
    "progress.bible": [
        "https://progress.bible",
        "https://progress.bible/about/partners/",
        "https://progress.bible/products/",
    ],
    "biblica.com": [
        "https://biblica.com",
        "https://biblica.com/about/",
    ],
    "sim.org": [
        "https://sim.org",
        "https://sim.org/about/",
    ],
    "wycliffe.org": [
        "https://wycliffe.org",
        "https://wycliffe.org/partners",
    ],
    "tbsbibles.org": [
        "https://www.tbsbibles.org",
        "https://www.tbsbibles.org/page/languages",
    ],
    "orality.net": [
        "https://orality.net",
    ],
    "aqua.sil.org": [
        "https://aqua.sil.org",
    ],
}

# Already known — don't re-list
KNOWN_DOMAINS = {
    "facebook.com", "twitter.com", "x.com", "instagram.com", "linkedin.com",
    "youtube.com", "youtu.be", "vimeo.com", "tiktok.com",
    "google.com", "googleapis.com", "googletagmanager.com", "google-analytics.com",
    "cloudflare.com", "cloudfront.net", "amazonaws.com", "akamaihd.net",
    "stripe.com", "paypal.com",
    # Sites already in resource-websites.md
    "bible.is", "faithcomesbyhearing.com", "dbs.org", "globalrecordings.net",
    "megavoice.com", "davaraudiobibles.org", "audioscripture.org",
    "bible.com", "scriptureearth.org", "find.bible", "ebible.org", "biblegateway.com",
    "kalanga.bible",
    "wycliffe.org", "sil.org", "unitedbiblesocieties.org", "tbsbibles.org",
    "biblesociety.org", "rca.org",
    "ai.sil.org", "missional.ai", "lelapa.ai",
    "gpt.sabda.org", "center.sabda.org",
    "talkingbibles.org", "fivefish.org", "theovision.org", "renewoutreach.com",
    "deafbiblesociety.com", "doorinternational.org", "deafmissions.com", "spoken.org",
    "americanbible.org", "biblica.com", "bibleleague.org", "bibleleague.ca",
    "crossway.org", "citybibles.com", "thedigitalbiblelibrary.org", "global.bible",
    "die-bibel.de", "biblesociety.org.au", "biblesociety.ca", "biblesociety.org.nz",
    "biblia.ru", "bible.or.jp", "bskorea.or.kr", "ubscp.org",
    "alliancebiblique.fr", "sbb.org.br", "sociedadebiblica.org", "sociedade-biblica.pt",
    "elkalima.com", "bijbelgenootschap.nl",
    "wycliffe.net", "seedcompany.com", "unfoldingword.org", "us.lbt.org",
    "pioneerbible.org", "ethnos360.org", "twftw.org", "ttionline.org",
    "sim.org", "cru.org", "ywam.org", "scriptureunion.org",
    "forum-intl.org", "ifobamexico.org", "eten.bible", "illuminations.bible",
    "intouch.org", "ibtrussia.org", "jaars.org", "lifewords.global",
    "storyrunners.com", "wholewordinstitute.com", "jcbt.org", "jerusalemseminary.org",
    "btfellowship.org", "davarpartners.org", "communitybiblestudy.org", "vom.org",
    "onehope.net", "progress.bible", "globalmediaoutreach.com",
    "museumofthebible.org", "faithward.org",
    "etenlab.org", "biblionexus.org", "tools.bible", "gloo.com",
    "etenlab.substack.com", "btconference.org", "isi.edu",
    "canil.ca", "taylor.edu",
    "harpercollinschristian.com", "zondervan.com", "thomasnelson.com", "faithgateway.com",
    "studygateway.com", "churchsource.com", "masterlectures.zondervanacademic.com",
    "mundocristao.com.br", "life.church", "armedservicesministry.org",
    "biblebox.org", "cvglobal.co", "bibleaccesslist.org", "store.bibleleague.org",
    "academiadabiblia.org.br", "sbb.com.br", "lojadabiblia.pt", "biblia.pt",
    "lojabiblica.pt", "open.bible", "docs.api.bible", "esv.org", "virtualstorehouse.org",
    "lbt.org", "ethnos360aviation.org", "ethnos360training.org",
    "imb.org", "frontiersusa.org", "pioneers.org", "samaritanspurse.org",
    "allianceforunreached.org", "indigitous.org", "teamexpansion.org",
    "perspectives.org", "joshuaproject.net", "orality.net", "jesusfilm.org",
    "biblesforchina.org", "missionexus.org", "askamissionary.com",
    "rightnowmedia.org", "wycliffe.org.za", "cabtal.org", "gillbt.com",
    "antba.org", "btlkenya.org", "nbtt.org.ng", "onebook.ca",
    "wycliffe.org.uk", "wycliffe.de", "wycliffe.ca", "wycliffe.org.au",
    "paratext.org", "scriptureforge.org", "software.sil.org",
    "autographamt.com", "semanticdictionary.org", "pubassist.paratext.org",
    "digitaltraininglibrary.org", "scripts.sil.org",
    "wibilex.de", "wirelex.de", "weltbibelhilfe.de", "bibelonline.de",
    "bibleproject.com", "awana.org", "worldvision.org", "compassion.com",
    "logos.com", "ethnologue.com", "absgift.org",
    "aqua.sil.org",
    # Skip these too
    "tharlam.app", "gsungrab.org", "createseeds.org",
    "wikipedia.org", "creativecommons.org", "github.com", "huggingface.co",
}


def root_domain(url: str) -> str:
    """Extract root domain (without subdomain) for dedup."""
    h = urlparse(url).hostname or ""
    if h.startswith("www."):
        h = h[4:]
    return h


def main() -> None:
    new_links: dict[str, list[tuple[str, str]]] = defaultdict(list)  # domain -> [(url, source_site)]

    for site, urls in TARGETS.items():
        rprint(f"\n[bold cyan]>>> {site}[/bold cyan]")
        for u in urls:
            try:
                res = scrape(u)
            except ScrapeError as e:
                rprint(f"  [red]FAIL {u}:[/red] {e}")
                continue
            outbound = extract_links(res.html, u)
            site_root = root_domain(u)
            rprint(f"  [dim]{u}[/dim] → {res.tier} ({len(outbound)} links)")
            for link in outbound:
                d = root_domain(link)
                if not d or d == site_root or d in KNOWN_DOMAINS:
                    continue
                if any(kd in d for kd in KNOWN_DOMAINS):  # subdomain check
                    continue
                new_links[d].append((link, site))

    out_path = Path(__file__).resolve().parents[1] / "data" / "crawl_unlocked.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({d: list(set(urls)) for d, urls in new_links.items()}, indent=2))
    rprint(f"\n[green]Wrote {out_path}[/green] ({len(new_links)} new domains)")

    rprint("\n[bold]NEW DOMAINS (deduped) — top 50 by hit count:[/bold]")
    sorted_d = sorted(new_links.items(), key=lambda kv: -len(kv[1]))
    for d, hits in sorted_d[:50]:
        sources = sorted({src for _, src in hits})
        sample = hits[0][0]
        rprint(f"  [cyan]{d}[/cyan] ({len(hits)} hits, from: {','.join(sources)})")
        rprint(f"      {sample[:100]}")


if __name__ == "__main__":
    main()
