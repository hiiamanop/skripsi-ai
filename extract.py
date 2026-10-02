#!/usr/bin/env python3
"""Ekstraksi: jawab tiap RQ + skor QA per paper included.
Tulis slr/<project>/extraction.csv (file,title,answers_rq1..N,qa_score).

Pakai:  .venv/bin/python extract.py <project> [-n maks] [--redo]
"""
import argparse
import csv
import json
import os

from pypdf import PdfReader

import config
import llm

RQ_PROMPT = """Jawab tiap RQ dari paper berikut. Jawab JSON saja: {{"answers_rq1": ..., ...}}.
RQ:
{rq}
Paper:
{text}"""

QA_PROMPT = """QA: nilai tiap item 0/1 dari paper berikut. Jawab JSON saja: {{"qa_id": 0/1}}.
Checklist:
{qa}
Paper:
{text}"""


def answer_rq(text, questions):
    rq = "\n".join(f"RQ{i + 1}: {q}" for i, q in enumerate(questions))
    raw, _ = llm.chat([{"role": "user", "content": RQ_PROMPT.format(rq=rq, text=text[:15000])}])
    return json.loads(raw[raw.find("{"):raw.rfind("}") + 1])


def score_qa(text, checklist):
    qa = "\n".join(f"{c['id']}: {c['question']}" for c in checklist)
    raw, _ = llm.chat([{"role": "user", "content": "QA:" + QA_PROMPT.format(qa=qa, text=text[:15000])}])
    got = json.loads(raw[raw.find("{"):raw.rfind("}") + 1])
    return sum(got.get(c["id"], 0) * c.get("weight", 1) for c in checklist)


def main():
    a = argparse.ArgumentParser()
    a.add_argument("project")
    a.add_argument("-n", type=int, default=0)
    a.add_argument("--redo", action="store_true")
    a = a.parse_args()

    proj = f"{config.SLR_DIR}/{a.project}"
    proto = json.load(open(f"{proj}/protocol.json"))
    n_rq = len(proto["research_questions"])
    fields = ["file", "title"] + [f"answers_rq{i + 1}" for i in range(n_rq)] + ["qa_score"]
    out = f"{proj}/extraction.csv"
    done = set()
    if os.path.exists(out) and not a.redo:
        with open(out) as f:
            done = {r["file"] for r in csv.DictReader(f)}
    inc = [r["file"] for r in csv.DictReader(open(f"{proj}/decisions.csv"))
           if r["phase"] == "fulltext" and r["decision"] == "include" and r["file"] not in done]
    if a.max:
        inc = inc[:a.max]
    new = not os.path.exists(out) or a.redo
    with open(out, "w" if new else "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        if new:
            w.writeheader()
        for i, pdf in enumerate(inc, 1):
            try:
                pages = PdfReader(f"{config.PAPERS_DIR}/{pdf}").pages
                text = "\n".join((p.extract_text() or "") for p in pages)
                ans = answer_rq(text, proto["research_questions"])
                qa = score_qa(text, proto["qa_checklist"])
                w.writerow({"file": pdf, "title": text.split("\n")[0][:200],
                            **{f"answers_rq{j + 1}": ans.get(f"answers_rq{j + 1}", "")
                               for j in range(n_rq)}, "qa_score": qa})
                print(f"[{i}/{len(inc)}] OK {pdf} qa={qa}")
            except Exception as e:
                print(f"[{i}/{len(inc)}] GAGAL {pdf}: {str(e)[:120]}")


if __name__ == "__main__":
    main()
