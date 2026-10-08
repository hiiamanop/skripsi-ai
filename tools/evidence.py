"""Pilih bukti dari hasil query Chroma dan format sitasi. Fungsi murni, tanpa jaringan."""
import re

import config


def cite(m):
    """Label sitasi dari metadata chunk: 'Wei dkk. 2025, hlm. 6' (hlm. 0 = abstrak)."""
    names = [n.strip() for n in (m.get("authors") or "").split(" and ") if n.strip()]
    last = [n.split()[-1] for n in names]
    who = (last[0] if len(last) == 1 else f"{last[0]} dan {last[1]}" if len(last) == 2
           else f"{last[0]} dkk.") if last else (m.get("title") or m.get("file", "?"))[:40]
    year = m.get("year") or "t.t."
    page = "abstrak" if m.get("page") == 0 else f"hlm. {m.get('page')}"
    return f"{who} {year}, {page}"


def is_reference_list(text):
    # ponytail: heuristik, >=4 tahun dalam satu chunk ~ daftar pustaka. Ganti dengan deteksi heading bila meleset.
    return (len(re.findall(r"\b(?:19|20)\d{2}\b", text)) >= 4
            and len(re.findall(r"\bpp\.?\s*\d|\bet al\b|\bIn:|\bProceedings\b|\bvol\.", text)) >= 2)


def select(res, k=config.TOP_K, max_dist=config.MAX_DIST):
    """res = hasil col.query. Return [(dist, meta, teks)] lolos ambang jarak dan bukan daftar pustaka."""
    rows = zip(res["distances"][0], res["metadatas"][0], res["documents"][0])
    return [r for r in rows if r[0] <= max_dist and not is_reference_list(r[2])][:k]


def build_context(sel):
    return "\n\n".join(f"[S{i}] ({cite(m)})\n{t}" for i, (_, m, t) in enumerate(sel, 1))


def cited_ids(answer, n):
    """(id valid yang dikutip, id di luar S1..Sn)."""
    ids = {int(x) for x in re.findall(r"\[S(\d+)\]", answer)}
    return sorted(i for i in ids if 1 <= i <= n), sorted(i for i in ids if not 1 <= i <= n)
