#!/usr/bin/env python3
"""Ingest papers/*.pdf -> chunk -> embed (OpenRouter) -> Chroma.

Pakai:  python3 ingest.py [-n maks] [--reindex]
"""
import argparse
import os

import chromadb
from pypdf import PdfReader

import config
import llm


def chunks(text, size=config.CHUNK_SIZE, overlap=config.CHUNK_OVERLAP):
    out, i = [], 0
    while i < len(text):
        out.append(text[i:i + size])
        i += size - overlap
    return [c for c in out if c.strip()]


def main():
    a = argparse.ArgumentParser()
    a.add_argument("-n", "--max", type=int, default=0)
    a.add_argument("--reindex", action="store_true")
    a = a.parse_args()

    db = chromadb.PersistentClient(path=config.CHROMA_DIR)
    if a.reindex:
        try:
            db.delete_collection(config.COLLECTION)
        except ValueError:
            pass
    col = db.get_or_create_collection(config.COLLECTION)

    pdfs = sorted(f for f in os.listdir(config.PAPERS_DIR) if f.endswith(".pdf"))
    if a.max:
        pdfs = pdfs[:a.max]
    print(f"{len(pdfs)} PDF")
    for f in pdfs:
        done = col.get(where={"file": f}, limit=1)["ids"]
        if done:
            print(f"skip {f}")
            continue
        text = "\n".join((p.extract_text() or "") for p in PdfReader(f"{config.PAPERS_DIR}/{f}").pages)
        cs = chunks(text)
        vecs = llm.embed(cs)
        col.add(ids=[f"{f}#{i}" for i in range(len(cs))],
                embeddings=vecs, documents=cs,
                metadatas=[{"file": f, "chunk": i} for i in range(len(cs))])
        print(f"OK {f} ({len(cs)} chunk)")


if __name__ == "__main__":
    main()
