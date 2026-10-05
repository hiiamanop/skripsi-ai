#!/usr/bin/env python3
"""Screening semi-otomatis 2 fase: LLM skor, user putuskan y/n.

Tulis slr/<project>/decisions.csv (file,source,phase,decision,reason,qa_score).

Pakai:  .venv/bin/python screen.py <project> [--phase title_abstract|fulltext] [--auto --min-score 80]
"""
import argparse
import csv
import json
import os

from pypdf import PdfReader

import config
import llm
from grabbers import detect_source

DECISION_FIELDS = ["file", "source", "phase", "decision", "reason", "qa_score"]

SCORE_PROMPT = """Kamu reviewer SLR. Nilai relevansi paper ini 0-100.
RQ: {rq}
Inklusi: {inc}
Eksklusi: {exc}
Judul: {title}
Abstrak: {abstract}
Jawab JSON saja: {{"score": N, "reason": "1 kalimat"}}"""


def score_paper(title, abstract, rq, inc, exc):
    raw, _ = llm.chat([{"role": "user", "content": SCORE_PROMPT.format(
        rq=rq, inc=inc, exc=exc, title=title, abstract=abstract[:2000])}])
    d = json.loads(raw[raw.find("{"):raw.rfind("}") + 1])
    return {"score": max(0, min(100, int(d["score"]))), "reason": d.get("reason", "")}


def full_text_of(path):
    r = PdfReader(path)
    return "\n".join((p.extract_text() or "") for p in r.pages)


def main():
    a = argparse.ArgumentParser()
    a.add_argument("project")
    a.add_argument("--phase", choices=["title_abstract", "fulltext"], default="title_abstract")
    a.add_argument("--auto", action="store_true")
    a.add_argument("--min-score", type=int, default=80)
    a = a.parse_args()

    proj = f"{config.SLR_DIR}/{a.project}"
    proto = json.load(open(f"{proj}/protocol.json"))
    dec_path = f"{proj}/decisions.csv"
    seen = set()
    if os.path.exists(dec_path):
        with open(dec_path) as f:
            seen = {(r["file"], r["phase"]) for r in csv.DictReader(f)}

    files = sorted(f for f in os.listdir(config.PAPERS_DIR) if f.endswith(".pdf"))
    if a.phase == "fulltext":
        passed = {r["file"] for r in csv.DictReader(open(dec_path))
                  if r["phase"] == "title_abstract" and r["decision"] == "include"}
        files = [f for f in files if f in passed]
    files = [f for f in files if (f, a.phase) not in seen]
    import time as _t
    with open(dec_path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=DECISION_FIELDS)
        if not seen:
            w.writeheader()
            f.flush()
        for pdf in files:
            text = full_text_of(f"{config.PAPERS_DIR}/{pdf}")
            if a.phase == "title_abstract":
                text = "\n".join(text.split("\n")[:60])
            for attempt in range(3):  # retry API 3x
                try:
                    s = score_paper(text.split("\n")[0][:200], text,
                                    proto["research_questions"], proto["inclusion"], proto["exclusion"])
                    break
                except Exception as e:
                    print(f"retry {attempt + 1} {pdf}: {str(e)[:100]}", flush=True)
                    _t.sleep(5 * (attempt + 1))
            else:
                print(f"LEWAT {pdf}: API gagal 3x", flush=True)
                continue
            if a.auto and s["score"] >= a.min_score:
                dec = "include"
            else:
                print(f"\n{pdf}\nskor={s['score']} {s['reason']}", flush=True)
                try:
                    dec = "include" if input("include? [y/N] ").lower() == "y" else "exclude"
                except EOFError:
                    dec = "exclude"  # non-interaktif: skor rendah tanpa konfirmasi = buang
            w.writerow({"file": pdf, "source": detect_source(pdf),
                        "phase": a.phase, "decision": dec,
                        "reason": f"[{s['score']}] " + s["reason"], "qa_score": ""})
            f.flush()
            print(f"{dec}: {pdf}", flush=True)


if __name__ == "__main__":
    main()
