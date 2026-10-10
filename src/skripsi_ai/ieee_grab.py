#!/usr/bin/env python3
"""Grab semua PDF open access dari URL hasil search IEEE Xplore.

Pakai:  python3 ieee_grab.py "<url search IEEE | queryText>" [-p proyek] [-o folder] [-n maks] [-d delay]
Stdlib only.
"""
import argparse, http.cookiejar, json, os, re, sys, time
import urllib.error, urllib.parse, urllib.request

from . import config
from . import papermeta
from .grabbers import BaseGrabber

BASE = "https://ieeexplore.ieee.org"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124 Safari/537.36"
LIST_KEYS = {"refinements", "ranges", "returnFacets"}  # param yang bentuknya array di API

jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
op.addheaders = [("User-Agent", UA)]


def build_payload(arg):
    if arg.startswith("http"):
        return arg, payload_from_url(arg)
    ref = BASE + "/search/searchresult.jsp?queryText=" + urllib.parse.quote(arg)
    return ref, {"queryText": arg, "openAccess": True}


def payload_from_url(url):
    qs = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    p = {}
    for k, v in qs.items():
        if k in LIST_KEYS:
            p[k] = v
        else:
            x = v[0]
            p[k] = {"true": True, "false": False}.get(x.lower(), int(x) if x.isdigit() else x)
    # paksa hanya open access bila belum di-set
    p.setdefault("openAccess", True)
    return p


def search(url, p, page, rows=100):
    body = dict(p, pageNumber=page, rowsPerPage=rows)
    req = urllib.request.Request(
        BASE + "/rest/search", json.dumps(body).encode(),
        {"Content-Type": "application/json", "Accept": "application/json",
         "Origin": BASE, "Referer": url})
    with op.open(req, timeout=60) as r:
        return json.load(r)


def download(rec, path):
    ar = rec["articleNumber"]
    req = urllib.request.Request(
        f"{BASE}/stampPDF/getPDF.jsp?tp=&isnumber=&arnumber={ar}",
        headers={"Referer": f"{BASE}/document/{ar}"})
    with op.open(req, timeout=120) as r:
        data = r.read()
    if not data.startswith(b"%PDF"):
        raise ValueError("bukan PDF (diblokir/butuh login?)")
    with open(path, "wb") as f:
        f.write(data)


def fname(rec):
    t = re.sub(r"<[^>]+>", "", rec.get("articleTitle", "untitled"))
    t = re.sub(r"[^\w\- ]+", "", t).strip()[:100]
    return f"{rec.get('publicationYear', '')}_{rec['articleNumber']}_{t}.pdf"


class IeeeGrabber(BaseGrabber):
    source = "ieee"

    def run(self, query_or_url, out, max_n=0, delay=2.0):
        os.makedirs(out, exist_ok=True)
        url, p = build_payload(query_or_url)
        op.open(url, timeout=60).read()  # ambil cookie sesi
        ok = skip = fail = seen = 0
        page = 1
        while True:
            try:
                d = search(url, p, page)
            except urllib.error.URLError as e:
                raise RuntimeError(f"search gagal: {e}")
            recs = d.get("records") or []
            if not recs:
                break
            if page == 1:
                print(f"Total hasil: {d.get('totalRecords')}")
            for r in recs:
                if max_n and seen >= max_n:
                    break
                seen += 1
                path = os.path.join(out, fname(r))
                if os.path.exists(path):
                    skip += 1
                    continue
                if r.get("accessType", {}).get("type") != "open-access":
                    skip += 1
                    continue
                try:
                    download(r, path)
                    papermeta.save(path, papermeta.from_ieee(r))
                    ok += 1
                    print(f"[{seen}] OK   {os.path.basename(path)}")
                except Exception as e:
                    fail += 1
                    print(f"[{seen}] GAGAL {r['articleNumber']}: {e}")
                time.sleep(delay)
            if (max_n and seen >= max_n) or page >= d.get("totalPages", 0):
                break
            page += 1
        print(f"Selesai. ok={ok} skip={skip} gagal={fail} -> {out}/")
        return ok, skip, fail


def main():
    a = argparse.ArgumentParser()
    a.add_argument("query_or_url")
    a.add_argument("-o", "--out", default=None, help="folder tujuan (default: papers/ proyek)")
    a.add_argument("-n", "--max", type=int, default=0, help="batas jumlah paper (0 = semua)")
    a.add_argument("-d", "--delay", type=float, default=2.0, help="jeda antar download (detik)")
    config.add_project_arg(a)
    a = a.parse_args()
    out = a.out or config.project_from(a).ensure().papers
    try:
        IeeeGrabber().run(a.query_or_url, out, a.max, a.delay)
    except Exception as e:
        sys.exit(f"gagal: {e}")


if __name__ == "__main__":
    main()
