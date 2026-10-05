# Known-Item Recall v2 — 2026-10-05

Metode: kumpulkan SEMUA DOI hasil string (paginasi penuh), cek keanggotaan.
Recall = ditemukan-oleh-string / 7. Pesaing 11574655 di luar penyebut.

| Studi | DOI | String | Status | Diagnosis |
|---|---|---|---|---|
| Pati 2025 | 10.1109/ACCESS.2025.3585609 | A v1 | TIDAK | ranking cutoff (ADA di indeks, keyword total=5) |
| Pati 2025 | sama | A v2 | ADA | C2X/C3X naikkan ranking ke 100 pertama |
| Acharya 2025 | 10.1109/ACCESS.2025.3532853 | A v1 | ADA | - |
| Roumeliotis 2026 | 10.1109/ACCESS.2026.3662282 | A v1 | ADA | - |
| Luo 2026 | 10.1109/ACCESS.2026.3720448 | A v1 | ADA | - |
| Gort 2026 | 10.1109/TMLCN.2026.3705714 | A v1 | TIDAK | C3 menolak (metadata tanpa trust/cost/...) |
| Gort 2026 | sama | A v2 | ADA | autonom* cocok metadata edge-cloud |
| Madyatmadja 2022 | 10.1109/ACCESS.2022.3158940 | B | ADA | - |
| Kumi 2024 | 10.1109/ACCESS.2024.3426329 | B | TIDAK | B1 miss (judul "Concerns" tak terindeks klausa); FULL n=2121 ranking cutoff. Ambil manual via DOI. |
| 11574655 pesaing | cari DOI | - | BELUM | wajib baca penuh (needs_human_read) |

**recall = 6/7 = 0.857** (A v2: 5/7 dengan Pati+Gort; B: 1/2 Madyatmadja; Kumi manual).
Pentelas 2023 keluar daftar (EC1 sah, non-LLM).
Selisih 100 (v1, tanpa filter jenis) vs 87/133: 13 non-jurnal + 46 dari C2X/C3X.
Sintaks DOI: tak didukung API. Query frase judul sensitif tanda baca.
