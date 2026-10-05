#!/usr/bin/env python3
"""Cek konsistensi PRISMA dari CSV. Exit 1 bila tak cocok.

Pakai:  .venv/bin/python reconcile.py <project>
"""
import csv
import sys
from collections import Counter

import config


def main():
    proj = f"{config.SLR_DIR}/{sys.argv[1]}"
    log = list(csv.DictReader(open(f"{proj}/search_log.csv")))
    dec = list(csv.DictReader(open(f"{proj}/decisions.csv")))
    ext = list(csv.DictReader(open(f"{proj}/extraction.csv")))
    noev = {r["id"] for r in csv.DictReader(open(f"{proj}/no_evaluation.csv"))}
    errs = []
    ta = [r for r in dec if r["phase"] == "title_abstract"]
    ft = [r for r in dec if r["phase"] == "fulltext"]
    if len(ta) != sum(int(r.get("retrieved", 0) or 0) for r in log if (r.get("retrieved") or "").isdigit()):
        errs.append(f"screened {len(ta)} != retrieved log")
    passed = {r["id"] for r in ta if r["decision"] in ("INCLUDE", "UNSURE")}
    orph = [r["id"] for r in ft if r["id"] not in passed]
    if orph:
        errs.append(f"fulltext tanpa lolos: {orph[:3]}")
    if {r["id"] for r in ext} | noev != {r["id"] for r in ft if r["decision"] == "INCLUDE"}:
        errs.append("extraction+noeval != fulltext INCLUDE")
    for code, n in Counter(r["criterion"] for r in ft if r["decision"] == "EXCLUDE").items():
        print(f"  out-ft {code}: {n}")
    prim = {r["id"] for r in ext} - noev
    print(f"identified={len(ta)} ft={len(ft)} primer={len(prim)} noeval={len(noev)}")
    if errs:
        print("GAGAL:"); [print(" -", e) for e in errs]
        sys.exit(1)
    print("OK konsisten")


if __name__ == "__main__":
    main()
