"""Fetch release pages that block Cloudflare Workers and hand the items to the release-watch Worker.

Perplexity and xAI sit behind Cloudflare bot rules that refuse requests from Workers and from
Python's default TLS fingerprint. curl_cffi impersonates Chrome's fingerprint, which gets through.
The Worker owns all state (what has been seen) and sends the Telegram alerts; this script only
fetches. Needs RW_INGEST_KEY in the environment.
"""
import json, os, re, sys, time
from curl_cffi import requests

WORKER = "https://release-watch.noqodepro.workers.dev/ingest"
KEY = os.environ["RW_INGEST_KEY"]
SOURCES = [
    {"id": "perplexity-changelog", "url": "https://www.perplexity.ai/changelog", "base": "https://www.perplexity.ai",
     "link_regex": r'href="(/changelog/[a-z0-9]+(?:-[a-z0-9]+)+)"'},
    {"id": "xai-news", "url": "https://x.ai/news", "base": "https://x.ai",
     "link_regex": r'href="(/news/[a-z0-9]+(?:-[a-z0-9]+)*)"'},
]


def get(url):
    err = None
    for delay in (0, 5, 15):  # the Cloudflare challenge is intermittent, a retry usually passes
        time.sleep(delay)
        try:
            r = requests.get(url, impersonate="chrome", timeout=30)
            if r.status_code == 200:
                return r.text
            err = f"HTTP {r.status_code}"
        except Exception as e:
            err = str(e)[:80]
    raise RuntimeError(err)


def items(src):
    out = []
    for p in re.findall(src["link_regex"], get(src["url"])):
        url = src["base"] + p
        if url not in [i["id"] for i in out]:
            out.append({"id": url, "title": url.rstrip("/").split("/")[-1].replace("-", " "), "link": url})
    return out


def title(url, fallback):
    try:
        html = get(url)
        m = (re.search(r'<meta[^>]+property="og:title"[^>]+content="([^"]+)"', html)
             or re.search(r"<title[^>]*>(.*?)</title>", html, re.S))
        t = re.sub(r"\s+", " ", m.group(1)).strip() if m else ""
        return t.replace("&amp;", "&").replace("&#x27;", "'") or fallback
    except Exception:
        return fallback


def ingest(payload):
    r = requests.post(WORKER, json=payload, headers={"x-key": KEY}, timeout=60)
    r.raise_for_status()
    return r.json()


failed = 0
for src in SOURCES:
    try:
        its = items(src)
        if not its:
            raise RuntimeError("0 items parsed, the page layout may have changed")
        new = set(ingest({"src": src["id"], "items": its, "dry": True}))  # ids the Worker has not seen
        fresh = [dict(i, title=title(i["link"], i["title"])) for i in its if i["id"] in new]
        log = ingest({"src": src["id"], "items": [i for i in its if i["id"] not in new] + fresh, "titled": True}) if new else []
        print(f"[{src['id']}] {len(its)} items, {len(new)} new", *log, sep="\n  ")
    except Exception as e:
        failed += 1
        print(f"[{src['id']}] FAILED: {e}")
sys.exit(1 if failed == len(SOURCES) else 0)  # a red run (GitHub emails the owner) only when nothing worked
