#!/usr/bin/env python3
"""Uji G1-G6 v2: kontra-bukti dari k_map kode + novelty_risk.md.

Pakai:  .venv/bin/python gaps3.py <project>
"""
import argparse
import csv
import json
import re

import config
import llm

GAPS = """G1 (RQ1): trust belum bergantung tugas, konteks, waktu
G2 (RQ2): konflik antaragen tidak dibedakan jenis dan dampak
G3 (RQ4): kebijakan belum terpadu dengan trust, konflik, biaya
G4 (RQ3): biaya dan latensi dilaporkan, belum jadi variabel keputusan
G5 (RQ3+RQ4): eskalasi manusia tanpa kriteria dan ukuran beban
G6 (RQ5+RQ6): tidak ada evaluasi orkestrasi multi-agen pada pengaduan publik; ketahanan jarang diuji"""

KMAP = {"G1": "K1", "G2": "K2", "G3": "K4", "G4": "K3", "G5": "K3", "G6": "K5"}


def parse_kmap(s):
    return dict(re.findall(r"['\"]?(K\d)['\"]?\s*:\s*['\"]?([A-Z ]+)['\"]?", s or ""))


def main():
    a = argparse.ArgumentParser()
    a.add_argument("project")
    a = a.parse_args()
    proj = f"{config.SLR_DIR}/{a.project}"
    rows = [r for r in csv.DictReader(open(f"{proj}/extraction.csv"))
            if r.get("tier") == "INTI" and r.get("reading") == "FULLTEXT"
            and float(r.get("qa3") or 0) > 0]
    # kontra-bukti dari kode
    contra = {}
    for g, k in KMAP.items():
        hits = []
        for r in rows:
            st = parse_kmap(r.get("k_map", "")).get(k, "")
            if st in ("TERTUTUP", "PARSIAL"):
                ev = (r.get("k_evidence") or "")[:200]
                hits.append(f"{r['id'][:45]} [{st}] {ev}")
        contra[g] = hits
    table = "\n".join(
        f"{r['id'][:45]} | RQ:{(r.get('rq_map') or '')[:150]} | K:{(r.get('k_map') or '')[:150]} | "
        f"H:{(r.get('results') or '')[:150]} | L:{(r.get('limitation_quote') or '')[:120]} "
        f"({r.get('limitation_page', '')})" for r in rows)
    clines = "\n".join(f"{g} kontra dari kode ({len(h)}):\n" + "\n".join(h[:10]) for g, h in contra.items())
    prompt = ("Uji G1-G6 berikut. Kontra-bukti dari kode sudah dihitung — PAKAI, jangan tulis 'tidak ada' "
              "bila daftar tak kosong.\nFormat per gap: pernyataan; Pendukung (INTI FULLTEXT + kutipan limitasi sendiri + halaman); "
              "Kontra-bukti (dari daftar); Kekuatan (kuat/sedang/sementara/TERTUTUP); "
              "Cakupan: 'dalam artikel jurnal open access IEEE Xplore 2021-2026 yang ditelaah'.\n"
              f"Hipotesis:\n{GAPS}\nKontra:\n{clines[:8000]}\nEkstraksi:\n{table[:20000]}")
    raw, via = llm.chat([{"role": "user", "content": prompt}])
    open(f"{proj}/gaps.md", "w").write(raw)
    # novelty_risk dari kode langsung (tanpa LLM)
    with open(f"{proj}/novelty_risk.md", "w") as f:
        f.write("# Tabel Risiko Kebaruan per K1-K5\n\n")
        for k in ["K1", "K2", "K3", "K4", "K5"]:
            f.write(f"## {k}\n")
            hits = [(r["id"][:60], parse_kmap(r.get("k_map", "")).get(k, ""), (r.get("k_evidence") or "")[:150])
                    for r in rows if parse_kmap(r.get("k_map", "")).get(k, "") in ("TERTUTUP", "PARSIAL")]
            if not hits:
                f.write("Tidak ada studi INTI menutup/menutup sebagian.\n")
            for hid, st, ev in hits:
                f.write(f"- [{st}] {hid} — {ev}\n")
    print(f"OK gaps.md via {via} ({len(rows)} INTI)")


if __name__ == "__main__":
    main()
