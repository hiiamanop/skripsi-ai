#!/usr/bin/env python3
"""Screening SLR ketat: putusan INCLUDE/EXCLUDE/UNSURE + kode IC/EC.

Kolom decisions.csv: id,doi,title,year,phase,decision,criterion,reason,reviewer.

Pakai:  .venv/bin/python screen2.py <project> <papers_dir> [--phase title_abstract|fulltext] [--auto]
"""
import argparse
import csv
import json
import os
import time

from pypdf import PdfReader

import config
import llm

FIELDS = ["id", "doi", "title", "year", "content_type", "phase", "decision", "criterion", "reason", "tier", "reviewer"]

PROMPT = """Kamu auditor SLR yang SKEPTIS. Default EXCLUDE kecuali bukti eksplisit di teks.
Putuskan SATU: INCLUDE / EXCLUDE / UNSURE.
RQ: {rq}
Inklusi: {inc}
Eksklusi: {exc}
Aturan: EC1 (multi-agent klasik tanpa LLM eksplisit) HANYA untuk track=A (string agentic).
Untuk track=B (pengaduan publik): LLM tidak wajib; nilai via IC1 jalur pengaduan + IC2 metode.
Judul: {title}
Teks: {text}
Survei agentic AI BUKAN EC1 (type survey, tetap INCLUDE bila relevan).
Tier: INTI bila substantif K1-K4/K5/pengaduan; KONTEKS bila aplikasi lain tanpa mekanisme itu.
INCLUDE wajib sebut SLR-RQ mana + bukti teks (alasan hanya IC4 ditolak).
Jawab JSON saja: {{"decision": "...", "criterion": "IC1/EC1/...", "reason": "1 kalimat + RQ",
"tier": "INTI/KONTEKS", "uses_llm": "ya/tidak", "doi": "... atau kosong",
"content_type": "...", "is_survey": true/false}}"""


def judge(title, text, proto, track):
    msg = {"role": "user", "content": PROMPT.format(
        rq="\n".join(proto["research_questions"]),
        inc="\n".join(proto["inclusion"]), exc="\n".join(proto["exclusion"]),
        title=f"[{track}] "+title, text=text[:3000])}
    raw, _ = llm.chat([msg])
    s = raw[raw.find("{"):raw.rfind("}") + 1]
    try:
        return json.loads(s, strict=False)
    except json.JSONDecodeError:
        fix = {"role": "user", "content": "Ulangi sebagai JSON valid saja."}
        raw2, _ = llm.chat([msg, {"role": "assistant", "content": raw}, fix])
        s2 = raw2[raw2.find("{"):raw2.rfind("}") + 1]
        return json.loads(s2, strict=False)


def text_of(path, max_lines=80):
    r = PdfReader(path)
    return "\n".join((p.extract_text() or "") for p in r.pages[:3])[:8000]


def main():
    a = argparse.ArgumentParser()
    a.add_argument("project")
    a.add_argument("papers_dir")
    a.add_argument("--phase", choices=["title_abstract", "fulltext"], default="title_abstract")
    a.add_argument("--track", choices=["A", "B"], default="A")
    a.add_argument("--auto", action="store_true")
    a = a.parse_args()

    proj = f"{config.SLR_DIR}/{a.project}"
    proto = json.load(open(f"{proj}/protocol.json"))
    dec_path = f"{proj}/decisions.csv"
    seen = set()
    if os.path.exists(dec_path) and os.path.getsize(dec_path):
        with open(dec_path) as f:
            seen = {(r["id"], r["phase"]) for r in csv.DictReader(f)}

    files = sorted(f for f in os.listdir(a.papers_dir) if f.endswith(".pdf"))
    if a.phase == "fulltext":
        passed = {r["id"] for r in csv.DictReader(open(dec_path))
                  if r["phase"] == "title_abstract" and r["decision"] in ("INCLUDE", "UNSURE")}
        files = [f for f in files if f in passed]
    files = [f for f in files if (f, a.phase) not in seen]
    print(f"{len(files)} file antri ({a.phase})")
    with open(dec_path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if f.tell() == 0:
            w.writeheader()
            f.flush()
        for pdf in files:
            year = pdf[:4] if pdf[:4].isdigit() else ""
            for attempt in range(3):
                try:
                    j = judge(pdf, text_of(f"{a.papers_dir}/{pdf}"), proto, a.track)
                    break
                except Exception as e:
                    print(f"retry {attempt + 1} {pdf}: {str(e)[:80]}", flush=True)
                    time.sleep(5 * (attempt + 1))
            else:
                print(f"LEWAT {pdf}", flush=True)
                continue
            dec = j.get("decision", "UNSURE").upper()
            if dec not in ("INCLUDE", "EXCLUDE", "UNSURE"):
                dec = "UNSURE"
            if not a.auto and dec != "EXCLUDE":
                print(f"\n{pdf}\nAI: {dec} [{j.get('criterion')}] {j.get('reason')}", flush=True)
                try:
                    ans = input("keputusan [I]nclude/[E]xclude/[U]nsure (Enter=ikut AI)? ").lower()
                    dec = {"i": "INCLUDE", "e": "EXCLUDE", "u": "UNSURE"}.get(ans, dec)
                except EOFError:
                    pass
            w.writerow({"id": pdf, "doi": j.get("doi", ""), "title": pdf, "year": year,
                        "content_type": j.get("content_type", ""),
                        "phase": a.phase, "decision": dec, "criterion": j.get("criterion", ""),
                        "reason": j.get("reason", ""), "tier": j.get("tier", ""), "reviewer": "agen"})
            f.flush()
            print(f"{dec}: {pdf}", flush=True)


if __name__ == "__main__":
    main()
