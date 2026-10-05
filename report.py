#!/usr/bin/env python3
"""Laporan SLR: decisions.csv -> prisma.svg + report.md.

Pakai:  .venv/bin/python report.py <project>
"""
import argparse
import csv
from collections import Counter

import config

def short_reason(reason):
    """Kelompokkan alasan exclude ke kategori singkat untuk PRISMA."""
    r = reason.lower()
    if any(k in r for k in ("trust", "confidence", "governance", "kalibrasi", "kepercayaan",
                            "pengukuran")):
        return "trust/governance tak dibahas"
    if any(k in r for k in ("metode", "method", "evaluasi", "experiment")):
        return "metode/evaluasi tak jelas"
    if any(k in r for k in ("tahun", "year", "bahasa", "language", "konferensi", "preprint")):
        return "di luar kriteria inklusi"
    if any(k in r for k in ("fokus utama", "kurang jelas", "tidak cukup", "uav", "robot",
                            "kesehatan", "hr ", "pertahanan", "v2x", "farmako")):
        return "di luar fokus RQ"
    return "lainnya: " + reason[5:85]  # lewati prefix [skor]


BOX_W, BOX_H, GAP = 320, 54, 18


def prisma_counts(rows):
    """Hitung angka PRISMA dari decisions.csv rows."""
    ident = Counter(r["source"] for r in rows if r["phase"] == "title_abstract")
    ta_ex = sum(1 for r in rows if r["phase"] == "title_abstract" and r["decision"] == "exclude")
    ft = [r for r in rows if r["phase"] == "fulltext"]
    ft_ex = sum(1 for r in ft if r["decision"] == "exclude")
    reasons = Counter(short_reason(r["reason"]) for r in ft if r["decision"] == "exclude")
    return {
        "by_source": dict(ident),
        "identified_total": sum(ident.values()),
        "excluded_title_abstract": ta_ex,
        "assessed_fulltext": len(ft),
        "excluded_fulltext": ft_ex,
        "excluded_reasons": dict(reasons),
        "included": sum(1 for r in ft if r["decision"] == "include"),
    }


def prisma_svg(c):
    """Render diagram alir PRISMA sederhana (kotak + panah vertikal), stdlib."""
    boxes = [
        f"Identification: {c['identified_total']} records "
        + ", ".join(f"{k}={v}" for k, v in c["by_source"].items()),
        f"Title/abstract screened, excluded {c['excluded_title_abstract']}",
        f"Full-text assessed: {c['assessed_fulltext']}, excluded {c['excluded_fulltext']}",
        f"Included: {c['included']}",
    ]
    h = len(boxes) * (BOX_H + GAP) + GAP
    cx = 20 + BOX_W // 2
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{BOX_W + 40}" height="{h}">']
    y = GAP
    for i, b in enumerate(boxes):
        if i:
            parts.append(
                f'<line x1="{cx}" y1="{y - GAP}" x2="{cx}" y2="{y}" stroke="black"/>'
                f'<polygon points="{cx - 5},{y - 8} {cx + 5},{y - 8} {cx},{y}" fill="black"/>')
        parts.append(
            f'<rect x="20" y="{y}" width="{BOX_W}" height="{BOX_H}" fill="white" stroke="black"/>'
            f'<text x="30" y="{y + 30}" font-size="13">{b[:52]}</text>')
        y += BOX_H + GAP
    parts.append("</svg>")
    return "\n".join(parts)


def main():
    a = argparse.ArgumentParser()
    a.add_argument("project")
    a = a.parse_args()
    proj = f"{config.SLR_DIR}/{a.project}"
    rows = list(csv.DictReader(open(f"{proj}/decisions.csv")))
    c = prisma_counts(rows)
    open(f"{proj}/prisma.svg", "w").write(prisma_svg(c))
    with open(f"{proj}/report.md", "w") as f:
        f.write(f"# Laporan SLR: {a.project}\n\nIdentified: {c['identified_total']} "
                f"({c['by_source']})\n\nExcluded title/abstract: {c['excluded_title_abstract']}\n\n"
                f"Full-text: {c['assessed_fulltext']}, excluded: {c['excluded_fulltext']} "
                f"{c['excluded_reasons']}\n\n**Included: {c['included']}**\n")
    print(f"OK {proj}/prisma.svg {proj}/report.md")


if __name__ == "__main__":
    main()
