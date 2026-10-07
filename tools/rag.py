#!/usr/bin/env python3
"""Tanya RAG: retrieve Chroma -> jawab via OpenRouter (fallback Ollama).

Pakai:  python3 rag.py "pertanyaan" [-k top_k]
"""
import argparse

import chromadb

import config
import llm

SYSTEM = ("Jawab berdasarkan konteks jurnal berikut. "
          "Sertakan sitasi [nama_file] tiap klaim penting.")


def main():
    a = argparse.ArgumentParser()
    a.add_argument("question")
    a.add_argument("-k", type=int, default=config.TOP_K)
    a = a.parse_args()

    col = chromadb.PersistentClient(path=config.CHROMA_DIR).get_collection(config.COLLECTION)
    q = llm.embed([a.question])[0]
    res = col.query(query_embeddings=[q], n_results=a.k)
    ctx = "\n\n".join(f"[{m['file']} #{m['chunk']}]\n{d}"
                      for d, m in zip(res["documents"][0], res["metadatas"][0]))
    ans, via = llm.chat([
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": f"Konteks:\n{ctx}\n\nPertanyaan: {a.question}"}])
    print(f"(via {via})\n{ans}")


if __name__ == "__main__":
    main()
