#!/usr/bin/env python3
"""Grab PDF open access dari link OpenAlex atau query mentah.

Pakai:  .venv/bin/python openalex_grab.py "<url openalex | query>" [-p proyek] [-o folder] [-n maks] [-d delay]
Stdlib only.
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

import config
import papermeta
from grabbers import BaseGrabber

API = "https://api.openalex.org/works"
UA = "SkripsiAI/1.0 (mailto:research@example.com)"


def build_params(arg):
    """Return dict param API dari link openalex atau query mentah."""
    if arg.startswith("http"):
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(arg).query)
        p = {k: v[0] for k, v in qs.items()}
    else:
        p = {"search": arg}
    f = p.get("filter", "")
    if "is_oa" not in f:
        p["filter"] = f + ",is_oa:true" if f else "is_oa:true"
    p["per-page"] = 100
    return p


def search(params, page, mailto=None):
    q = dict(params, page=page)
    if mailto:
        q["mailto"] = mailto
    req = urllib.request.Request(API + "?" + urllib.parse.urlencode(q), headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def pdf_urls(w):
    """Semua kandidat URL PDF OA: best dulu, lalu lokasi lain."""
    urls = []
    loc = w.get("best_oa_location") or {}
    if loc.get("pdf_url"):
        urls.append(loc["pdf_url"])
    for l in w.get("locations") or []:
        if l.get("is_oa") and l.get("pdf_url") and l["pdf_url"] not in urls:
            urls.append(l["pdf_url"])
    return urls


def fname(w):
    year = w.get("publication_year", "")
    oid = (w.get("id") or "").split("/")[-1]
    t = re.sub(r"[^\w\- ]+", "", w.get("display_name") or "untitled").strip()[:100]
    return f"{year}_{oid}_{t}.pdf"


BROWSER_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
              "Chrome/124 Safari/537.36")


def download(url, path):
    req = urllib.request.Request(url, headers={"User-Agent": BROWSER_UA, "Referer": "https://openalex.org/"})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = r.read()
    if not data.startswith(b"%PDF"):
        raise ValueError("bukan PDF")
    with open(path, "wb") as f:
        f.write(data)


class OpenAlexGrabber(BaseGrabber):
    source = "openalex"

    def run(self, query_or_url, out="papers/openalex", max_n=0, delay=1.0, mailto=None):
        os.makedirs(out, exist_ok=True)
        params = build_params(query_or_url)
        ok = skip = fail = seen = page = 0
        page = 1
        while True:
            d = search(params, page, mailto)
            if page == 1:
                print(f"Total hasil: {d['meta']['count']}")
            works = d.get("results") or []
            if not works:
                break
            for w in works:
                if max_n and seen >= max_n:
                    break
                seen += 1
                path = os.path.join(out, fname(w))
                if os.path.exists(path):
                    skip += 1
                    continue
                urls = pdf_urls(w)
                if not urls:
                    skip += 1
                    continue
                err = None
                for url in urls:  # coba tiap lokasi OA sampai dapat
                    try:
                        download(url, path)
                        papermeta.save(path, papermeta.from_openalex(w))
                        ok += 1
                        print(f"[{seen}] OK   {os.path.basename(path)}")
                        break
                    except Exception as e:
                        err = e
                else:
                    fail += 1
                    print(f"[{seen}] GAGAL {w.get('id')}: {str(err)[:100]}")
                time.sleep(delay)
            if (max_n and seen >= max_n) or page * 100 >= d["meta"]["count"]:
                break
            page += 1
        print(f"Selesai. ok={ok} skip={skip} gagal={fail} -> {out}/")
        return ok, skip, fail


def main():
    a = argparse.ArgumentParser()
    a.add_argument("query_or_url")
    a.add_argument("-o", "--out", default=None, help="folder tujuan (default: papers/ proyek)")
    a.add_argument("-n", "--max", type=int, default=0)
    a.add_argument("-d", "--delay", type=float, default=1.0)
    a.add_argument("--mailto", default=None)
    config.add_project_arg(a)
    a = a.parse_args()
    out = a.out or config.project_from(a).ensure().papers
    try:
        OpenAlexGrabber().run(a.query_or_url, out, a.max, a.delay, a.mailto)
    except Exception as e:
        sys.exit(f"gagal: {e}")


if __name__ == "__main__":
    main()
