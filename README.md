# Skripsi-AI

Research partner pribadi untuk skripsi / tesis / disertasi. Visi: kumpulkan artikel, baca, simpan ke vector DB, lalu setiap jawaban dan keputusan riset berbasis bukti dari referensi yang terkumpul.

Status: prototipe CLI di `tools/` (jalankan dari root repo).

| Tahap | Tool |
|---|---|
| Kumpul PDF | `ieee_grab.py`, `openalex_grab.py` (deteksi sumber: `grabbers.py`) |
| Indeks ke vector DB | `ingest.py` |
| Tanya berbasis bukti | `rag.py` |
| Ringkas ke CSV | `summarize.py` |
| BibTeX | `crossref.py`, `bibtex.py`, `export_bib.py` |

Konfigurasi di `.env` (lihat `.env.example`). Tes: `pytest -q tests`.
