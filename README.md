# Skripsi-AI

Aplikasi bantu menyiapkan skripsi / tesis / disertasi. Sedang dirancang ulang dari awal.

Tools yang sudah ada di `tools/` (dijalankan dari root repo): ambil PDF jurnal (`ieee_grab.py`, `openalex_grab.py`), indeks vektor + tanya (`ingest.py`, `rag.py`, `summarize.py`), BibTeX (`bibtex.py`, `crossref.py`, `export_bib.py`), PRISMA (`report.py`, `reconcile.py`), protokol (`slr_init.py`).

Konfigurasi di `.env` (lihat `.env.example`). Tes: `pytest -q tests`.
