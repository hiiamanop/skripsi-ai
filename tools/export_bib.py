#!/usr/bin/env python3
"""Export literature.csv -> references.bib (BibTeX).

Pakai:  .venv/bin/python export_bib.py
"""
import csv
import re

rows = list(csv.DictReader(open("literature.csv")))
with open("references.bib", "w") as f:
    for r in rows:
        if not r.get("title"):
            continue
        key = re.sub(r"\W+", "", (r["authors"].split(",")[0].split() or ["x"])[-1] + r.get("year", ""))
        f.write(f"@article{{{key},\n  title={{{r['title']}}},\n"
                f"  author={{{r['authors']}}},\n  year={{{r.get('year', '')}}},\n"
                f"  doi={{{r.get('doi', '')}}},\n  file={{{r['file']}}}\n}}\n\n")
print(f"{len(rows)} baris -> references.bib")
