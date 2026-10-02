# SLR Tool: Kitchenham + PRISMA — Design Spec

Tanggal: 2026-10-02. Status: disetujui user per bagian, belum implementasi.

## 1. Tujuan
Tools CLI bantu SLR end-to-end (planning → conducting → reporting)
Kitchenham + laporan PRISMA 2020. Pengguna umum, multi-sumber paper.

## 2. Struktur proyek
```
papers/{source}/{file}.pdf     # hasil grab per sumber (ieee, scopus, ...)
slr/{project}/
  protocol.json                # RQ, IC/EC, QA checklist (diisi user)
  decisions.csv                # screening per fase + alasan
  extraction.csv               # ekstraksi data (reuse literature.csv + answers_rqN + qa_score)
```

## 3. Alur kerja (4 CLI)
1. `slr_init.py <nama>` — buat `slr/<nama>/` + template `protocol.json`.
2. Grab per sumber → `papers/{source}/`.
   - IEEE: `ieee_grab.py` ada. Tambah `--source ieee` agar output ke `papers/ieee/`.
   - Sumber lain: interface `BaseGrabber`; stub bila perlu API key/manual + catat alasan.
   - Deteksi sumber dari domain link (ieeexplore→ieee, scopus→scopus, else→other).
3. `screen.py` — deduplikasi (DOI/judul) → screening 2 fase (`--phase title_abstract|fulltext`;
   fase 2 hanya review yang lolos fase 1; LLM skor, user putuskan). Tulis `decisions.csv`.
4. `extract.py` — jawab tiap RQ + skor QA per paper included → `extraction.csv`
   (kolom `file,title,answers_rq1..N,qa_score`).
5. `gaps.py` — `extraction.csv` → LLM sintesis gap → `gaps.md`
   (tabel gap + kandidat RQ baru, topik jenuh, kontradiksi).
6. `report.py` — `decisions.csv` → diagram PRISMA (SVG stdlib) + tabel + BibTeX.

## 4. Skema data
- `protocol.json`: `research_questions[]`, `inclusion[]`, `exclusion[]`,
  `qa_checklist[{id, question, weight}]`.
- `decisions.csv`: `file, source, phase(title_abstract|fulltext), decision(include|exclude), reason, qa_score`.
- `extraction.csv`: kolom `literature.csv` + `answers_rq{1..n}`, `qa_score`.
- Kolom `source` wajib: bahan hitungan PRISMA identification per database.

## 5. Teknologi
Stack existing: CLI Python, Chroma, OpenRouter (embed `qwen/qwen3-embedding-8b`,
chat `gpt-4o-mini` → fallback Ollama), pypdf. Diagram PRISMA: SVG murni stdlib
(tanpa matplotlib/graphviz — alasan: nol dep, portable; revisit bila butuh styling).

## 6. Non-tujuan (YAGNI)
Web UI, multi-user, Qdrant, embedding lokal, auto-screening penuh tanpa user.
