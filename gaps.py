#!/usr/bin/env python3
"""Analisis research gap dari extraction.csv -> gaps.md.
Minta LLM: topik jenuh vs jarang, kontradiksi, limitasi berulang, kandidat RQ baru.

Pakai:  .venv/bin/python gaps.py <project>
"""
import argparse
import csv
import json

import config
import llm

GAP_PROMPT = """Kamu analis SLR. Dari tabel ekstraksi berikut, tulis markdown:
## Research Gaps (tabel: Gap | Bukti file | Kandidat RQ baru)
## Topik Jenuh (1 paragraf)
## Kontradiksi antar paper (bila ada)
RQ: {rq}
Ekstraksi:
{table}"""


def analyze_gaps(rows, questions):
    table = "\n".join(
        f"{r['file']}: " + "; ".join(f"{k}={r.get(k, '')}" for k in r if k.startswith("answers_"))
        for r in rows)
    raw, _ = llm.chat([{"role": "user", "content": GAP_PROMPT.format(
        rq=questions, table=table[:15000])}])
    return raw


def main():
    a = argparse.ArgumentParser()
    a.add_argument("project")
    a = a.parse_args()
    proj = f"{config.SLR_DIR}/{a.project}"
    proto = json.load(open(f"{proj}/protocol.json"))
    rows = list(csv.DictReader(open(f"{proj}/extraction.csv")))
    md = analyze_gaps(rows, proto["research_questions"])
    open(f"{proj}/gaps.md", "w").write(md)
    print(f"OK {proj}/gaps.md ({len(rows)} paper dianalisis)")


if __name__ == "__main__":
    main()
