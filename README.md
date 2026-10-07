# Skripsi-AI

Tools bantu susun skripsi/SLR: ambil PDF jurnal IEEE open access, RAG, SLR Kitchenham + PRISMA, BibTeX.

Jalankan semua dari root repo: `.venv/bin/python tools/<skrip>.py`. Config di `.env` (lihat `.env.example`).

## Alur
| Langkah | Skrip |
|---|---|
| Ambil PDF IEEE OA / OpenAlex | `tools/ieee_grab.py`, `tools/openalex_grab.py` (+ `grabbers.py`) |
| Indeks + tanya (Chroma) | `tools/ingest.py`, `tools/rag.py`, `tools/summarize.py` |
| Siapkan protokol SLR | `tools/slr_init.py` |
| Screening (track A/B, 2 fase) | `tools/screen2.py` |
| Ekstraksi + QA | `tools/extract2.py` |
| Uji gap dari kode | `tools/gaps4.py` |
| Cek konsistensi PRISMA (exit non-zero bila beda) | `tools/reconcile.py <slr>` |
| PRISMA / laporan | `tools/report.py` |
| BibTeX (CrossRef) | `tools/bibtex.py`, `tools/export_bib.py` |

## Folder
- `slr/<nama>/` : hasil per SLR (di-ignore git; yang penting ditambah dengan `git add -f`). `slr/tesis_v3/` = SLR final tesis.
- `papers/` : PDF (di-ignore git).
- `docs/` : desain dan rencana. `tests/` : `pytest -q tests`.
