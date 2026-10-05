#!/usr/bin/env python3
"""Gaps v3 dari kode: pendukung INTI + kutipan relevan; label aturan ketat.

Aturan label: ada TERTUTUP -> TERTUTUP (sebagian/penuh); else PARSIAL/n>=3 -> sedang;
else sementara. EC4/KONTEKS/ABSTRACT_ONLY dilarang jadi pendukung.

Pakai:  .venv/bin/python gaps4.py <project>
"""
import csv
import re
import sys

import config

KMAP = {"G1": "K1", "G2": "K2", "G3": "K4", "G4": "K3", "G5": "K3", "G6": "K5"}
GAPS = {
    "G1": "trust belum bergantung tugas, konteks, waktu",
    "G2": "konflik antaragen tidak dibedakan jenis dan dampak",
    "G3": "kebijakan belum terpadu dengan trust, konflik, biaya",
    "G4": "biaya dan latensi dilaporkan, belum jadi variabel keputusan",
    "G5": "eskalasi manusia tanpa kriteria dan ukuran beban",
    "G6": "tidak ada evaluasi orkestrasi multi-agen pada pengaduan publik; ketahanan jarang diuji",
}


def kmap(s):
    return dict(re.findall(r"['\"]?(K\d)['\"]?\s*:\s*['\"]?([A-Z ]+)['\"]?", s or ""))


def main():
    proj = f"{config.SLR_DIR}/{sys.argv[1]}"
    rows = [r for r in csv.DictReader(open(f"{proj}/extraction.csv"))
            if r.get("tier") == "INTI" and r.get("reading") == "FULLTEXT"
            and float(r.get("qa3") or 0) > 0]
    L = ["# Uji Gap v3 (dari kode)\n", f"Sumber: {len(rows)} INTI FULLTEXT primer.\n"]
    for g, desc in GAPS.items():
        k = KMAP[g]
        closed = [(r["id"][:50], (r.get("k_evidence") or "")[:150])
                  for r in rows if kmap(r.get("k_map", "")).get(k) == "TERTUTUP"]
        part = [(r["id"][:50], (r.get("k_evidence") or "")[:150])
                for r in rows if kmap(r.get("k_map", "")).get(k) == "PARSIAL"]
        nok = [r for r in rows if kmap(r.get("k_map", "")).get(k, "TIDAK") in ("TIDAK", "TIDAK DITEMUKAN")
               and (r.get("limitation_quote") or "") != "TIDAK DITEMUKAN"]
        if closed:
            label = "TERTUTUP (sebagian)"
        elif len(part) >= 3 or len(nok) < 3:
            label = "sedang"
        else:
            label = "kuat" if len(nok) >= 3 else "sementara"
        L.append(f"## {g}: {desc} — **{label}**")
        L.append(f"Pendukung ({len(nok)}): " + "; ".join(
            f"{r['id'][:45]} `{((r.get('limitation_quote') or '')[:90])}`" for r in nok[:8]))
        L.append(f"Kontra TERTUTUP ({len(closed)}): " + ("; ".join(f"{i} `{e}`" for i, e in closed[:8]) or "-"))
        L.append(f"Kontra PARSIAL ({len(part)}): " + ("; ".join(f"{i} `{e}`" for i, e in part[:8]) or "-"))
        L.append("Cakupan: dalam artikel jurnal open access IEEE Xplore 2021–2026 yang ditelaah.\n")
    open(f"{proj}/gaps.md", "w").write("\n".join(L))
    print(f"OK gaps.md ({len(rows)} INTI)")


if __name__ == "__main__":
    main()
