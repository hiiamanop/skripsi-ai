#!/usr/bin/env python3
"""Tanya berbasis bukti: retrieve Chroma -> saring bukti -> jawab hanya dari bukti, tiap klaim bersitasi.

Bukti tak cukup (jarak di atas ambang) -> tidak memanggil LLM, menolak menjawab.
Setiap tanya dicatat di data/<proyek>/decisions.jsonl (pertanyaan, jawaban, bukti) untuk ditelusuri.

Pakai:  python3 tools/rag.py "pertanyaan" [-p proyek] [-k top_k] [--max-dist 0.4]
"""
import argparse
import json
import time

import config
import evidence
import llm
import store

SYSTEM = ("Kamu asisten riset. Jawab HANYA dari bukti [S1], [S2], ... yang diberikan. "
          "Tiap klaim diakhiri id bukti, mis. [S2]. Bila bukti tidak memuat jawabannya, "
          "katakan itu terus terang; jangan memakai pengetahuan di luar bukti. "
          "Bila bukti saling bertentangan, sebutkan keduanya.")


def log_decision(proj, rec):
    with open(f"{proj.dir}/decisions.jsonl", "a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def ask(proj, question, k=config.TOP_K, max_dist=config.MAX_DIST):
    """Return dict: status ('answered'|'no_evidence'), answer, evidence[]. Dicatat ke decisions.jsonl."""
    col = store.open_collection(proj)
    q = llm.embed([question])[0]
    res = col.query(query_embeddings=[q], n_results=max(k * 4, 20),
                    include=["documents", "metadatas", "distances"])
    sel = evidence.select(res, k, max_dist)
    rec = {"time": time.strftime("%Y-%m-%dT%H:%M:%S"), "question": question, "max_dist": max_dist,
           "best_dist": round(res["distances"][0][0], 3) if res["distances"][0] else None,
           "evidence": [{"id": f"S{i}", "cite": evidence.cite(m), "file": m["file"], "page": m["page"],
                         "dist": round(d, 3), "text": t} for i, (d, m, t) in enumerate(sel, 1)]}
    if not sel:
        rec.update(status="no_evidence", answer="", via="")
    else:
        ans, via = llm.chat([
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": f"Bukti:\n{evidence.build_context(sel)}\n\nPertanyaan: {question}"}])
        ok, bad = evidence.cited_ids(ans, len(sel))
        rec.update(status="answered", answer=ans, via=via, cited=ok, invalid_cites=bad)
    log_decision(proj, rec)
    return rec


def main():
    a = argparse.ArgumentParser()
    a.add_argument("question")
    a.add_argument("-k", type=int, default=config.TOP_K)
    a.add_argument("--max-dist", type=float, default=config.MAX_DIST)
    config.add_project_arg(a)
    a = a.parse_args()
    proj = config.project_from(a)

    try:
        r = ask(proj, a.question, a.k, a.max_dist)
    except Exception as e:
        if isinstance(e, SystemExit):
            raise
        raise SystemExit(f"proyek '{proj.name}' belum punya index ({str(e)[:80]}). Jalankan ingest.py -p {proj.name}")
    if r["status"] == "no_evidence":
        print(f"Bukti tidak cukup: jarak terbaik {r['best_dist']} > ambang {a.max_dist}. "
              "Koleksi tidak memuat topik ini. Tambah artikel (grab + ingest) atau ubah pertanyaan.")
        return
    print(f"(via {r['via']})\n{r['answer']}\n\nBukti:")
    for e in r["evidence"]:
        print(f"  [{e['id']}] {e['cite']} (jarak {e['dist']})")
    if r["invalid_cites"]:
        print(f"PERINGATAN: jawaban mengutip id tak ada: {r['invalid_cites']}")
    elif not r["cited"]:
        print("PERINGATAN: jawaban tanpa sitasi, jangan dipakai sebagai bukti.")


if __name__ == "__main__":
    main()
