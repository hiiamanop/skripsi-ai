#!/usr/bin/env python3
"""Uji hipotesis gap G1-G6 dari extraction.csv -> gaps.md.
Wajib kontra-bukti + kekuatan bukti + kutipan keterbatasan. Cakupan: IEEE OA ditelaah.

Pakai:  .venv/bin/python gaps2.py <project>
"""
import argparse
import csv
import json

import config
import llm

GAPS = """G1: trust belum bergantung tugas, konteks, waktu
G2: konflik antaragen tidak dibedakan jenis dan dampak
G3: kebijakan belum terpadu dengan trust, konflik, biaya
G4: biaya dan latensi dilaporkan, belum jadi variabel keputusan
G5: eskalasi manusia tanpa kriteria dan ukuran beban
G6: tidak ada evaluasi orkestrasi multi-agen pada pengaduan publik; ketahanan jarang diuji"""

PROMPT = """Kamu penguji gap SLR, bukan pembenar. Untuk tiap hipotesis G1-G6 tulis:
### Gn: pernyataan
- Pendukung: id studi + hasil/capaian relevan
- Kontra-bukti: studi yang justru sudah mengerjakan (jangan sembunyikan; bila tak ada tulis "tidak ada")
- Kekuatan: kuat|sedang|sementara
- Dasar: kutipan keterbatasan penulis (verbatim <=25 kata + halaman)
Semua gap nyatakan cakupannya: "dalam artikel jurnal open access IEEE yang ditelaah".
Bila studi menutup gap, laporkan eksplisit.
Hipotesis:
{gaps}
Ekstraksi (id | RQ-map | K-map | hasil | kutipan limitasi | QA):
{table}"""


def main():
    a = argparse.ArgumentParser()
    a.add_argument("project")
    a = a.parse_args()
    proj = f"{config.SLR_DIR}/{a.project}"
    rows = list(csv.DictReader(open(f"{proj}/extraction.csv")))
    lines = []
    for r in rows:
        lines.append(f"{r['id'][:50]} | RQ:{r.get('rq_map','')[:200]} | K:{r.get('k_map','')[:200]} | "
                     f"H:{(r.get('results') or '')[:200]} | L:{(r.get('limitation_quote') or '')[:120]} "
                     f"({r.get('limitation_page','')}) | QA:{r.get('qa1','')}{r.get('qa2','')}{r.get('qa3','')}")
    msg = {"role": "user", "content": PROMPT.format(gaps=GAPS, table="\n".join(lines)[:25000])}
    raw, via = llm.chat([msg])
    open(f"{proj}/gaps.md", "w").write(raw)
    print(f"OK {proj}/gaps.md via {via} ({len(rows)} paper)")


if __name__ == "__main__":
    main()
