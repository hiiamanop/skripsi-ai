# Skripsi-AI

Research partner pribadi untuk skripsi / tesis / disertasi. Visi: kumpulkan artikel, baca, simpan ke vector DB, lalu setiap jawaban dan keputusan riset berbasis bukti dari referensi yang terkumpul.

Status: prototipe CLI di `tools/` (jalankan dari root repo).

| Tahap | Tool |
|---|---|
| Kumpul PDF | `ieee_grab.py`, `openalex_grab.py`, `scopus_grab.py` (cari via Scopus incl. Elsevier OA, PDF via OpenAlex; perlu `ELSEVIER_API_KEY`) |
| Indeks ke vector DB | `ingest.py` |
| Tanya berbasis bukti | `rag.py` (sitasi `Penulis Tahun, hlm. X`, menolak jawab bila bukti lemah, log di `data/<proyek>/decisions.jsonl`) |
| Ringkas ke CSV | `summarize.py` |
| BibTeX | `crossref.py`, `bibtex.py`, `export_bib.py` |

Semua tool menerima `-p <proyek>` (default `default`). Satu proyek = satu folder `data/<proyek>/` berisi `papers/`, `chroma/`, `literature.csv`, `references.bib`, terisolasi dari proyek lain. Contoh:

```
python tools/openalex_grab.py "graph neural network" -p skripsi-a -n 20
python tools/ingest.py -p skripsi-a
python tools/rag.py "apa metode utamanya?" -p skripsi-a
```

Konfigurasi di `.env` (lihat `.env.example`). Tes: `pytest -q tests`.
