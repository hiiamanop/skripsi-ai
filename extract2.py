#!/usr/bin/env python3
"""Ekstraksi ketat tesis: verbatim + halaman, TIDAK DITEMUKAN, QA 0/0.5/1.

Kolom extraction.csv: id,doi,year,venue,type,domain,uses_llm_agent,objective,
method_data,method_model,method_metrics,method_baseline,results,rq_map,k_map,
limitation_quote,limitation_page,not_covered,qa1..qa6,reading,confidence.
qa.csv: ringkas skor QA per paper.

Pakai:  .venv/bin/python extract2.py <project> <papers_dir> [-n maks]
"""
import argparse
import csv
import json
import os
import time

from pypdf import PdfReader

import config
import llm

FIELDS = ["id", "doi", "year", "venue", "content_type", "type", "tier", "domain",
          "uses_llm_agent", "objective", "method_data", "method_model", "method_metrics",
          "method_baseline", "results", "rq_map", "k_map", "k_evidence",
          "limitation_quote", "limitation_page", "sections_scanned", "not_covered",
          "qa1", "qa2", "qa3", "qa4", "qa5", "qa6", "qa_total", "reading", "confidence"]

PROMPT = """Kamu ekstraktor SLR. Baca paper, jawab JSON saja. Aturan WAJIB:
- Setiap klaim metode/hasil WAJIB dari teks. Tidak ada di teks -> tulis "TIDAK DITEMUKAN".
- limitation_quote: kutipan verbatim penulis <=25 kata + limitation_page nomor halaman.
- qa1..qa6: 0 / 0.5 / 1. QA6=0 DILARANG bila rq_map tak kosong; studi fokus K1-K4 dapat 1.
- k_map: per K1-K5 tulis TERTUTUP / PARSIAL / TIDAK / TIDAK DITEMUKAN.
- k_evidence: kutipan + halaman tiap TERTUTUP/PARSIAL.
- sections_scanned: bagian yang dipindai (mis. Abstract, Limitations, Conclusion, Future Work).
- limitation_quote: KALIMAT UTUH verbatim <=25 kata (dilarang fragmen).
- type: survey|empiris|kerangka. reading: FULLTEXT. confidence: tinggi|sedang|rendah.
RQ: {rq}
Paper:
{text}
Skema: {{"doi":"","venue":"","content_type":"","type":"","domain":"","uses_llm_agent":"","objective":"",
"method_data":"","method_model":"","method_metrics":"","method_baseline":"","results":"",
"rq_map":"","k_map":"","k_evidence":"","limitation_quote":"","limitation_page":"",
"sections_scanned":"","not_covered":"",
"qa1":0,"qa2":0,"qa3":0,"qa4":0,"qa5":0,"qa6":0,"confidence":""}}"""


def extract(text, proto):
    msg = {"role": "user", "content": PROMPT.format(
        rq="\n".join(proto["research_questions"]), text=text[:25000])}
    raw, _ = llm.chat([msg])
    s = raw[raw.find("{"):raw.rfind("}") + 1]
    try:
        return json.loads(s, strict=False)
    except json.JSONDecodeError:
        fix = {"role": "user", "content": "Ulangi sebagai JSON valid saja."}
        raw2, _ = llm.chat([msg, {"role": "assistant", "content": raw}, fix])
        s2 = raw2[raw2.find("{"):raw2.rfind("}") + 1]
        return json.loads(s2, strict=False)


def full_text(path):
    r = PdfReader(path)
    out = []
    for i, p in enumerate(r.pages, 1):
        t = p.extract_text() or ""
        out.append(f"\n[Halaman {i}]\n{t}")
    return "\n".join(out)


def main():
    a = argparse.ArgumentParser()
    a.add_argument("project")
    a.add_argument("papers_dir")
    a.add_argument("-n", "--max", type=int, default=0)
    a = a.parse_args()

    proj = f"{config.SLR_DIR}/{a.project}"
    proto = json.load(open(f"{proj}/protocol.json"))
    out = f"{proj}/extraction.csv"
    done = set()
    if os.path.exists(out) and os.path.getsize(out):
        with open(out) as f:
            done = {r["id"] for r in csv.DictReader(f)}
    inc = [r["id"] for r in csv.DictReader(open(f"{proj}/decisions.csv"))
           if r["phase"] == "fulltext" and r["decision"] == "INCLUDE" and r["id"] not in done]
    if a.max:
        inc = inc[:a.max]
    print(f"{len(inc)} paper antri ekstraksi")
    with open(out, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if f.tell() == 0:
            w.writeheader()
            f.flush()
        for i, pdf in enumerate(inc, 1):
            for attempt in range(3):
                try:
                    d = extract(full_text(f"{a.papers_dir}/{pdf}"), proto)
                    break
                except Exception as e:
                    print(f"retry {attempt + 1} {pdf}: {str(e)[:80]}", flush=True)
                    time.sleep(5 * (attempt + 1))
            else:
                print(f"GAGAL {pdf}: 3x", flush=True)
                continue
            dec = next((r for r in csv.DictReader(open(f"{proj}/decisions.csv"))
                        if r["id"] == pdf), {})
            qa_tot = sum(float(d.get(f"qa{i}", 0) or 0) for i in range(1, 7))
            w.writerow({"id": pdf, "doi": dec.get("doi", ""), "year": pdf[:4],
                        "tier": dec.get("tier", ""), "qa_total": qa_tot, "reading": "FULLTEXT",
                        **{k: d.get(k, "") for k in FIELDS if k not in ("id", "doi", "year", "tier", "qa_total", "reading")}})
            f.flush()
            print(f"[{i}/{len(inc)}] OK {pdf}", flush=True)
    qa_rows = list(csv.DictReader(open(out)))
    with open(f"{proj}/qa.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id", "qa1", "qa2", "qa3", "qa4", "qa5", "qa6", "total"])
        w.writeheader()
        for r in qa_rows:
            tot = sum(float(r.get(f"qa{i}", 0) or 0) for i in range(1, 7))
            w.writerow({"id": r["id"], **{f"qa{i}": r.get(f"qa{i}", "") for i in range(1, 7)}, "total": tot})
    print(f"qa.csv ditulis ({len(qa_rows)} baris)")


if __name__ == "__main__":
    main()
