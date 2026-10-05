#!/usr/bin/env python3
"""extraction.csv -> references.bib via Crossref.

Pakai:  .venv/bin/python bibtex.py <project> [-n maks]
"""
import argparse
import csv
import re
import time

import config
import crossref

STOP = {"a", "an", "the", "for", "with", "using", "based", "via", "toward", "from",
        "multi", "agent", "agents", "agentic", "system", "systems", "framework"}


def keywords(pdf):
    """Kata kunci dari filename: buang tahun/id, stopwords, ambil 8."""
    name = re.sub(r"^\d+_\d+_", "", pdf)[:-4]
    words = [w for w in re.split(r"[\W_]+", name.lower()) if len(w) > 2 and w not in STOP]
    return " ".join(words[:8])


def key(authors, year, title):
    first = re.sub(r"\W+", "", (authors.split(" and ")[0].split() or ["x"])[-1])
    return f"{first}{year}{re.sub(r'\W+', '', title.split()[0])}"


def entry(i, meta, pdf):
    return (f"@article{{{key(meta['authors'], meta['year'], meta['title'])},\n"
            f"  author = {{{meta['authors']}}},\n  title = {{{meta['title']}}},\n"
            f"  journal = {{{meta['journal']}}},\n  year = {{{meta['year']}}},\n"
            f"  volume = {{{meta['volume']}}}, number = {{{meta['issue']}}},\n"
            f"  pages = {{{meta['pages']}}},\n  doi = {{{meta['doi']}}},\n"
            f"  url = {{{meta['url']}}},\n  file = {{{pdf}}}\n}}\n\n")


def main():
    a = argparse.ArgumentParser()
    a.add_argument("project")
    a.add_argument("-n", "--max", type=int, default=0)
    a = a.parse_args()
    proj = f"{config.SLR_DIR}/{a.project}"
    rows = list(csv.DictReader(open(f"{proj}/extraction.csv")))
    if a.max:
        rows = rows[:a.max]
    ok, miss = [], []
    for r in rows:
        pdf = r.get("file") or r.get("id", "")
        title = keywords(pdf)
        year = int(pdf[:4]) if pdf[:4].isdigit() else None
        print(f"cari: {title}")
        m = None
        for attempt in range(2):
            try:
                m = crossref.lookup(title, year)
                break
            except Exception as e:
                print(f"  retry: {str(e)[:60]}")
                time.sleep(5)
                if attempt == 1:
                    miss.append(f"{pdf} ({e})")
        if m:
            ok.append(entry(len(ok), m, pdf))
        elif pdf not in [x.split(" (")[0] for x in miss]:
            miss.append(pdf)
        time.sleep(2)
    ok = [e for e in ok if e]
    open(f"{proj}/references.bib", "w").write("".join(ok))
    print(f"OK {len(ok)}, tak ketemu {len(miss)} -> {proj}/references.bib")
    for m in miss:
        print("  MISS:", m[:100])


if __name__ == "__main__":
    main()
