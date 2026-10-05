#!/usr/bin/env python3
"""Audit independen via 9router model main. Prompt skeptis: default EXCLUDE.

Pakai:  .venv/bin/python audit2.py <project> <papers_dir>
Output: kolom audit_main, audit_criterion, audit_reason di audit_sample.csv
+ ringkasan setuju/tak-setuju vs keputusan agen.
"""
import csv
import json
import os
import time
import urllib.request

import config
from screen2 import text_of

URL = os.environ.get("NINEROUTER_URL", "http://localhost:20128")
KEY = os.environ.get("NINEROUTER_API_KEY", "")

PROMPT = """Kamu auditor SLR yang SKEPTIS. Default EXCLUDE kecuali bukti eksplisit di teks.
INCLUDE hanya bila SEMUA terpenuhi: (1) agen LLM/agentic eksplisit ATAU pengaduan publik;
(2) ada metode/kerangka yang dapat dianalisis; (3) relevan >=1 RQ berikut:
{rq}
EC1: multi-agent klasik tanpa LLM -> EXCLUDE (kecuali track B pengaduan publik).
Judul: {title}
Teks: {text}
Jawab JSON saja: {{"decision": "INCLUDE/EXCLUDE", "criterion": "IC/EC", "reason": "1 kalimat bukti"}}"""


def ask(title, text, rq):
    payload = {"model": "main", "messages": [
        {"role": "user", "content": PROMPT.format(rq=rq, title=title, text=text[:3000])}]}
    req = urllib.request.Request(f"{URL}/v1/chat/completions", json.dumps(payload).encode(),
                                 {"Content-Type": "application/json", "Authorization": f"Bearer {KEY}"})
    with urllib.request.urlopen(req, timeout=120) as r:
        raw = json.load(r)["choices"][0]["message"]["content"]
    return json.loads(raw[raw.find("{"):raw.rfind("}") + 1])


def main():
    import argparse
    a = argparse.ArgumentParser()
    a.add_argument("project")
    a.add_argument("papers_dir")
    a = a.parse_args()
    proj = f"{config.SLR_DIR}/{a.project}"
    proto = json.load(open(f"{proj}/protocol.json"))
    rq = "\n".join(proto["research_questions"])
    rows = list(csv.DictReader(open(f"{proj}/audit_sample.csv")))
    for r in rows:
        r.setdefault("audit_main", "")
        r.setdefault("audit_criterion", "")
        r.setdefault("audit_reason", "")
    agree = disagree = 0
    for r in rows:
        if r.get("audit_main"):
            agree += r["audit_main"] == r["ai_decision"]
            disagree += r["audit_main"] != r["ai_decision"]
            continue
        for attempt in range(3):
            try:
                j = ask(r["id"], text_of(f"{a.papers_dir}/{r['id']}"), rq)
                break
            except Exception as e:
                print(f"retry {r['id']}: {str(e)[:80]}", flush=True)
                time.sleep(5)
        else:
            print(f"GAGAL {r['id']}", flush=True)
            continue
        r["audit_main"] = j.get("decision", "")
        r["audit_criterion"] = j.get("criterion", "")
        r["audit_reason"] = j.get("reason", "")
        agree += r["audit_main"] == r["ai_decision"]
        disagree += r["audit_main"] != r["ai_decision"]
        print(f"{r['audit_main']} (AI: {r['ai_decision']}) {r['id'][:70]}", flush=True)
        time.sleep(1)
    with open(f"{proj}/audit_sample.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"setuju={agree} beda={disagree}")


if __name__ == "__main__":
    main()
