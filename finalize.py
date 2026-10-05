#!/usr/bin/env python3
"""Paket handoff SLR tesis: prisma.svg + cek konsistensi + limitations.md + ai_use_statement.md.

Pakai:  .venv/bin/python finalize.py <project>
Gagal (exit 1) bila alur PRISMA tak konsisten.
"""
import argparse
import csv
import sys
from collections import Counter

import config
from report import prisma_svg

BOX_W, BOX_H, GAP = 320, 54, 18


def main():
    a = argparse.ArgumentParser()
    a.add_argument("project")
    a = a.parse_args()
    proj = f"{config.SLR_DIR}/{a.project}"
    rows = list(csv.DictReader(open(f"{proj}/decisions.csv")))
    ta = [r for r in rows if r["phase"] == "title_abstract"]
    ft = [r for r in rows if r["phase"] == "fulltext"]
    ta_inc = sum(1 for r in ta if r["decision"] == "INCLUDE")
    ta_uns = sum(1 for r in ta if r["decision"] == "UNSURE")
    # cek 1: fulltext hanya dari yang lolos fase 1
    passed = {r["id"] for r in ta if r["decision"] in ("INCLUDE", "UNSURE")}
    orphans = [r["id"] for r in ft if r["id"] not in passed]
    assert not orphans, f"fulltext tanpa lolos fase1: {orphans}"
    # cek 2: jumlah fulltext = lolos fase 1
    assert len(ft) == ta_inc + ta_uns, f"fulltext {len(ft)} != lolos {ta_inc + ta_uns}"
    # cek 3: extraction = fulltext INCLUDE - EC4
    ext = list(csv.DictReader(open(f"{proj}/extraction.csv")))
    ft_inc = {r["id"] for r in ft if r["decision"] == "INCLUDE"}
    noeval = {r["id"] for r in csv.DictReader(open(f"{proj}/no_evaluation.csv"))} if __import__("os").path.exists(f"{proj}/no_evaluation.csv") else set()
    assert {r["id"] for r in ext} | noeval == ft_inc, "extraction+noeval != fulltext INCLUDE"
    by_src = Counter("B" if ("9733331" in r["id"] or "10511080" in r["id"] or "11550066" in r["id"]) else "A" for r in ta)
    c = {"by_source": dict(by_src), "identified_total": len(ta),
         "excluded_title_abstract": sum(1 for r in ta if r["decision"] == "EXCLUDE"),
         "assessed_fulltext": len(ft),
         "excluded_fulltext": sum(1 for r in ft if r["decision"] == "EXCLUDE"),
         "excluded_reasons": dict(Counter(r["criterion"] for r in ft if r["decision"] == "EXCLUDE")),
         "included": len(ft_inc)}
    open(f"{proj}/prisma.svg", "w").write(prisma_svg(c))
    with open(f"{proj}/report.md", "w") as f:
        f.write(f"# Laporan SLR: {a.project}\n\nIdentified: {c['identified_total']} ({c['by_source']})\n\n"
                f"Excluded title/abstract: {c['excluded_title_abstract']}\n\n"
                f"Full-text: {c['assessed_fulltext']}, excluded: {c['excluded_fulltext']} {c['excluded_reasons']}\n\n"
                f"**Included: {c['included']}** (primer: {len(ext)}, no-eval: {len(noeval)})\n")
    with open(f"{proj}/limitations.md", "w") as f:
        f.write("""# Keterbatasan SLR
- Satu basis data (IEEE Xplore); Scopus/DOAJ belum tersedia.
- String ditentukan user; sensitivitas query frase judul rendah (lihat known_item_check.md).
- Screening AI (9router main) + audit 12 sampel; 75% sampel awal GPT ditolak — screening GPT dibuang, diulang via main.
- Ekstraksi AI FULLTEXT; 20% audit manusia belum dilakukan (audit_sample.csv kolom human kosong).
- 2 studi EC4 tanpa evaluasi empiris dikeluarkan dari primer.
- Paper 2026 sangat baru: 6 tak terindeks Crossref (bibtex MISS).
""")
    with open(f"{proj}/ai_use_statement.md", "w") as f:
        f.write("""# Pernyataan Penggunaan AI
- Screening judul/abstrak + full-text: 9router main, prompt skeptis, putusan INCLUDE/EXCLUDE/UNSURE + kode IC/EC.
- Screening awal GPT-4o-mini dibuang (audit: 9/12 ditolak auditor independen).
- Ekstraksi: 9router main, FULLTEXT, kutipan verbatim <=25 kata + halaman; TIDAK DITEMUKAN bila absen.
- QA 6 item (0/0.5/1). Gap: uji G1-G6 dengan kontra-bukti wajib.
- Semua ML decision tercatat di decisions.csv (reviewer=agen). Verifikasi manusia: audit_sample.csv.
""")
    print(f"OK cek lolos. primer={len(ext)} noeval={len(noeval)}")
    print(f"PRISMA: {c['identified_total']} -> {c['excluded_title_abstract']} out -> {c['assessed_fulltext']} ft -> {c['included']} in")


if __name__ == "__main__":
    main()
