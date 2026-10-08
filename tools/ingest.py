#!/usr/bin/env python3
"""Ingest PDF proyek -> chunk per halaman -> embed (OpenRouter, per batch) -> Chroma.

Tiap chunk membawa metadata paper (judul, penulis, tahun, DOI) dan nomor halaman.
Abstrak (bila ada) jadi chunk tambahan dengan page=0.

Pakai:  python3 tools/ingest.py [-p proyek] [-n maks] [--reindex]
"""
import argparse
import os

from pypdf import PdfReader

import config
import llm
import papermeta
import store


def chunks(text, size=config.CHUNK_SIZE, overlap=config.CHUNK_OVERLAP):
    out, i = [], 0
    while i < len(text):
        out.append(text[i:i + size])
        i += size - overlap
    return [c for c in out if c.strip()]


def page_chunks(pages):
    """[(halaman 1-based, teks)]. ponytail: chunk tak melintasi batas halaman."""
    return [(n, c) for n, t in enumerate(pages, 1) for c in chunks(t)]


def embed_all(texts):
    out = []
    for i in range(0, len(texts), config.EMBED_BATCH):
        out += llm.embed(texts[i:i + config.EMBED_BATCH])
    return out


def ingest_one(col, f, pages, meta):
    """Embed semua dulu, baru tambah: gagal di tengah tak meninggalkan paper setengah jadi."""
    items = page_chunks(pages)
    if meta.get("abstract"):
        items.insert(0, (0, meta["abstract"]))
    if not items:
        return 0
    vecs = embed_all([t for _, t in items])
    base = {"file": f, "title": meta.get("title") or "", "authors": meta.get("authors") or "",
            "year": meta.get("year") or 0, "doi": meta.get("doi") or ""}
    col.add(ids=[f"{f}#{i}" for i in range(len(items))], embeddings=vecs,
            documents=[t for _, t in items],
            metadatas=[{**base, "chunk": i, "page": p} for i, (p, _) in enumerate(items)])
    return len(items)


def main():
    a = argparse.ArgumentParser()
    a.add_argument("-n", "--max", type=int, default=0)
    a.add_argument("--reindex", action="store_true")
    config.add_project_arg(a)
    a = a.parse_args()
    proj = config.project_from(a).ensure()
    col = store.open_collection(proj, create=True, reset=a.reindex)

    pdfs = sorted(f for f in os.listdir(proj.papers) if f.endswith(".pdf"))
    if a.max:
        pdfs = pdfs[:a.max]
    print(f"{len(pdfs)} PDF")
    for f in pdfs:
        if col.get(where={"file": f}, limit=1)["ids"]:
            print(f"skip {f}")
            continue
        path = f"{proj.papers}/{f}"
        try:
            pages = [p.extract_text() or "" for p in PdfReader(path).pages]
            meta = papermeta.resolve(path, pages[0] if pages else "")
            n = ingest_one(col, f, pages, meta)
        except Exception as e:
            print(f"GAGAL {f}: {str(e)[:100]}")
            continue
        note = "" if any(t.strip() for t in pages) else " [PDF tanpa teks (scan?), hanya abstrak]"
        print(f"{'OK' if n else 'KOSONG'} {f} ({n} chunk, meta={meta['source']}){note}")


if __name__ == "__main__":
    main()
