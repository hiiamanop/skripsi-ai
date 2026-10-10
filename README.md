# Skripsi-AI

Research partner pribadi untuk skripsi / tesis / disertasi. Visi: kumpulkan artikel, baca, simpan ke vector DB, lalu setiap jawaban dan keputusan riset berbasis bukti dari referensi yang terkumpul.

## Pakai

Butuh [uv](https://docs.astral.sh/uv/). Dari folder kerja skripsi Anda:

```
uvx skripsi-ai -p skripsi        # nama proyek bebas; data tersimpan di ./data/skripsi/
```

Isi `.env` di folder itu (kunci API tidak ikut paket):

```
OPENROUTER_API_KEY=...           # LLM dan embedding
ELSEVIER_API_KEY=...             # opsional, hanya untuk sumber Scopus
```

Dalam sesi, ketik biasa (cari artikel, index, tanya, catat keputusan) atau perintah `/bantuan`.
Lanjutkan sesi: `uvx skripsi-ai -p skripsi --resume`. Daftar sesi: `--sesi`.
Percakapan, jawaban berbukti, keputusan, dan catatan tersimpan di `data/<proyek>/memory.db`.

## Pengembangan

```
uv venv && uv pip install -e . pytest
.venv/bin/python run.py -p uji     # atau: python -m skripsi_ai
.venv/bin/python -m pytest -q tests
uv build                            # hasil di dist/
```

Kode ada di `src/skripsi_ai/`. Modul tunggal bisa dijalankan: `python -m skripsi_ai.ingest -p skripsi`.
