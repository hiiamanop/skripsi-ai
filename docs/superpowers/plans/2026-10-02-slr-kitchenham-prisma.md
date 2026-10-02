# SLR Kitchenham + PRISMA Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** CLI SLR end-to-end: init proyek → grab multi-sumber → screening semi-otomatis → laporan PRISMA SVG.

**Architecture:** 4 CLI independen baca/tulis file (`protocol.json`, `decisions.csv`, `extraction.csv`). Pola existing: argparse + `main()`, `llm.chat()` return `(text, via)`. Test: pytest, assert-based, file dummy di `/tmp`, tanpa sentuh `papers/`.

**Tech Stack:** Python stdlib + pypdf, chromadb, pytest. SVG stdlib untuk PRISMA.

**Spec:** `docs/slr-design.md`

## Task 5: `extract.py` ekstraksi jawaban RQ + QA (gantikan Non-Goal)

**Files:**
- Create: `extract.py`
- Test: `tests/test_slr.py` (tambah test)

**Interfaces:**
- Consumes: `protocol.json` (`research_questions`, `qa_checklist`) dari Task 1; `decisions.csv` phase=fulltext decision=include dari Task 3; `llm.chat()`; `config.PAPERS_DIR`
- Produces: `slr/<project>/extraction.csv` kolom `file,title,answers_rq1..N,qa_score`; dipakai Task 6 (`report.py`) untuk tabel sintesis.

- [ ] **Step 1: Write the failing test**

```python
def test_extract_qa(monkeypatch):
    from extract import answer_rq, score_qa
    monkeypatch.setattr("extract.llm", _FakeLLM_QA())
    a = answer_rq("full text ...", ["RQ1?", "RQ2?"])
    assert set(a) == {"answers_rq1", "answers_rq2"}
    assert all(a.values())
    s = score_qa("full text ...", [{"id": "qa1", "question": "Q?", "weight": 2}])
    assert s == 2
```

dengan helper di file test:

```python
class _FakeLLM_QA:
    def chat(self, messages):
        import json
        prompt = messages[0]["content"]
        if prompt.startswith("QA:"):
            return json.dumps({"qa1": 1}), "fake"
        return json.dumps({"answers_rq1": "jawaban 1", "answers_rq2": "jawaban 2"}), "fake"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_slr.py::test_extract_qa -v`
Expected: FAIL ("No module named 'extract'")

- [ ] **Step 3: Write minimal implementation**

```python
#!/usr/bin/env python3
"""Ekstraksi: jawab tiap RQ + skor QA per paper included.
Tulis slr/<project>/extraction.csv (file,title,answers_rq1..N,qa_score).

Pakai:  .venv/bin/python extract.py <project> [-n maks] [--redo]
"""
import argparse
import csv
import json
import os

from pypdf import PdfReader

import config
import llm

RQ_PROMPT = """Jawab tiap RQ dari paper berikut. Jawab JSON saja: {{"answers_rq1": ..., ...}}.
RQ:
{rq}
Paper:
{text}"""

QA_PROMPT = """QA: nilai tiap item 0/1 dari paper berikut. Jawab JSON saja: {{"qa_id": 0/1}}.
Checklist:
{qa}
Paper:
{text}"""


def answer_rq(text, questions):
    rq = "\n".join(f"RQ{i + 1}: {q}" for i, q in enumerate(questions))
    raw, _ = llm.chat([{"role": "user", "content": RQ_PROMPT.format(rq=rq, text=text[:15000])}])
    return json.loads(raw[raw.find("{"):raw.rfind("}") + 1])


def score_qa(text, checklist):
    qa = "\n".join(f"{c['id']}: {c['question']}" for c in checklist)
    raw, _ = llm.chat([{"role": "user", "content": "QA:" + QA_PROMPT.format(qa=qa, text=text[:15000])}])
    got = json.loads(raw[raw.find("{"):raw.rfind("}") + 1])
    return sum(got.get(c["id"], 0) * c.get("weight", 1) for c in checklist)


def main():
    a = argparse.ArgumentParser()
    a.add_argument("project")
    a.add_argument("-n", type=int, default=0)
    a.add_argument("--redo", action="store_true")
    a = a.parse_args()

    proj = f"{config.SLR_DIR}/{a.project}"
    proto = json.load(open(f"{proj}/protocol.json"))
    n_rq = len(proto["research_questions"])
    fields = ["file", "title"] + [f"answers_rq{i + 1}" for i in range(n_rq)] + ["qa_score"]
    out = f"{proj}/extraction.csv"
    done = set()
    if os.path.exists(out) and not a.redo:
        with open(out) as f:
            done = {r["file"] for r in csv.DictReader(f)}
    inc = [r["file"] for r in csv.DictReader(open(f"{proj}/decisions.csv"))
           if r["phase"] == "fulltext" and r["decision"] == "include" and r["file"] not in done]
    if a.max:
        inc = inc[:a.max]
    new = not os.path.exists(out) or a.redo
    with open(out, "w" if new else "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        if new:
            w.writeheader()
        for i, pdf in enumerate(inc, 1):
            try:
                pages = PdfReader(f"{config.PAPERS_DIR}/{pdf}").pages
                text = "\n".join((p.extract_text() or "") for p in pages)
                ans = answer_rq(text, proto["research_questions"])
                qa = score_qa(text, proto["qa_checklist"])
                w.writerow({"file": pdf, "title": text.split("\n")[0][:200],
                            **{f"answers_rq{j + 1}": ans.get(f"answers_rq{j + 1}", "")
                               for j in range(n_rq)}, "qa_score": qa})
                print(f"[{i}/{len(inc)}] OK {pdf} qa={qa}")
            except Exception as e:
                print(f"[{i}/{len(inc)}] GAGAL {pdf}: {str(e)[:120]}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_slr.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add extract.py tests/test_slr.py
git commit -m "feat: extract.py jawaban RQ + skor QA -> extraction.csv"
```

---

### Task 6: `gaps.py` analisis research gap

**Files:**
- Create: `gaps.py`
- Test: `tests/test_slr.py` (tambah test)

**Interfaces:**
- Consumes: `extraction.csv` (Task 5), `protocol.json` RQ (Task 1), `llm.chat()`
- Produces: `slr/<project>/gaps.md` (tabel gap + kandidat RQ baru); dibaca manusia, bukan mesin.

- [ ] **Step 1: Write the failing test**

```python
def test_gaps_format(monkeypatch):
    from gaps import analyze_gaps
    monkeypatch.setattr("gaps.llm", _FakeLLM_Gaps())
    rows = [
        {"file": "a.pdf", "title": "T1", "answers_rq1": "metode X untuk trust",
         "answers_rq2": "akurasi 90%", "qa_score": "3"},
        {"file": "b.pdf", "title": "T2", "answers_rq1": "metode X untuk trust",
         "answers_rq2": "akurasi 85%", "qa_score": "2"},
    ]
    md = analyze_gaps(rows, ["RQ1: metode apa?", "RQ2: hasil?"])
    assert "## Research Gaps" in md
    assert "a.pdf" in md or "metode X" in md
```

dengan helper di file test:

```python
class _FakeLLM_Gaps:
    def chat(self, messages):
        return ("## Research Gaps\n\n| Gap | Bukti | Kandidat RQ |\n"
                "|---|---|---|\n"
                "| metode X jenuh di trust | a.pdf, b.pdf | RQ baru: di luar trust? |\n"), "fake"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_slr.py::test_gaps_format -v`
Expected: FAIL ("No module named 'gaps'")

- [ ] **Step 3: Write minimal implementation**

```python
#!/usr/bin/env python3
"""Analisis research gap dari extraction.csv -> gaps.md.
Minta LLM: topik jenuh vs jarang, kontradiksi, limitasi berulang, kandidat RQ baru.

Pakai:  .venv/bin/python gaps.py <project>
"""
import argparse
import csv
import json

import config
import llm

GAP_PROMPT = """Kamu analis SLR. Dari tabel ekstraksi berikut, tulis markdown:
## Research Gaps (tabel: Gap | Bukti file | Kandidat RQ baru)
## Topik Jenuh (1 paragraf)
## Kontradiksi antar paper (bila ada)
RQ: {rq}
Ekstraksi:
{table}"""


def analyze_gaps(rows, questions):
    table = "\n".join(
        f"{r['file']}: " + "; ".join(f"{k}={r.get(k, '')}" for k in r if k.startswith("answers_"))
        for r in rows)
    raw, _ = llm.chat([{"role": "user", "content": GAP_PROMPT.format(
        rq=questions, table=table[:15000])}])
    return raw


def main():
    a = argparse.ArgumentParser()
    a.add_argument("project")
    a = a.parse_args()
    proj = f"{config.SLR_DIR}/{a.project}"
    proto = json.load(open(f"{proj}/protocol.json"))
    rows = list(csv.DictReader(open(f"{proj}/extraction.csv")))
    md = analyze_gaps(rows, proto["research_questions"])
    open(f"{proj}/gaps.md", "w").write(md)
    print(f"OK {proj}/gaps.md ({len(rows)} paper dianalisis)")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_slr.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add gaps.py tests/test_slr.py
git commit -m "feat: gaps.py analisis research gap -> gaps.md"
```

---

### Task 7: Integrasi + `.gitignore` + smoke test end-to-end

## Global Constraints

- Python 3.14, venv `.venv/`, test via `.venv/bin/python -m pytest`.
- Style: stdlib-first, no abstraksi tak diminta, fewest files.
- `llm.chat(messages)` return `(text, via)` — jangan ubah signature.
- Screening: semi-otomatis (LLM skor + user y/n), flag `--auto --min-score N` opsional.
- SVG PRISMA: stdlib only, tanpa matplotlib/graphviz.

---

### Task 1: `slr_init.py` + config `SLR_DIR`

**Files:**
- Create: `slr_init.py`
- Create: `tests/test_slr.py` (ditaruh Task ini, dipakai semua task)
- Modify: `config.py` (tambah `SLR_DIR = os.environ.get("SLR_DIR", "./slr")`)

**Interfaces:**
- Consumes: `config.SLR_DIR`
- Produces: `slr_init(project: str) -> str` return path proyek; dipakai Task 3-5 sebagai lokasi `protocol.json`/`decisions.csv`.

- [ ] **Step 1: Write the failing test**

```python
import json
import os
import shutil
import subprocess
import sys

PROJ = "/tmp/slr_test_proj"


def _run(*args):
    return subprocess.run(
        [sys.executable, "slr_init.py", *args],
        capture_output=True, text=True, cwd="/Users/ahmad/orca/projects/Skripsi-AI")


def test_init_creates_protocol():
    shutil.rmtree(PROJ, ignore_errors=True)
    r = _run("/tmp/slr_test_proj")
    assert r.returncode == 0, r.stderr
    with open(f"{PROJ}/protocol.json") as f:
        p = json.load(f)
    assert p["research_questions"] == []
    assert p["inclusion"] == []
    assert p["exclusion"] == []
    assert isinstance(p["qa_checklist"], list)
    shutil.rmtree(PROJ, ignore_errors=True)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_slr.py::test_init_creates_protocol -v`
Expected: FAIL (slr_init.py belum ada; jika pytest belum install: `.venv/bin/pip install pytest` dulu)

- [ ] **Step 3: Write minimal implementation**

```python
#!/usr/bin/env python3
"""Buat proyek SLR baru: slr/<nama>/protocol.json template.

Pakai:  .venv/bin/python slr_init.py <nama | path>
"""
import argparse
import json
import os

import config

TEMPLATE = {
    "research_questions": [],
    "inclusion": [],
    "exclusion": [],
    "qa_checklist": [{"id": "qa1", "question": "", "weight": 1}],
}


def slr_init(project):
    path = project if os.path.isabs(project) or "/" in project else f"{config.SLR_DIR}/{project}"
    os.makedirs(path, exist_ok=True)
    with open(f"{path}/protocol.json", "w") as f:
        json.dump(TEMPLATE, f, indent=2)
    return path


def main():
    a = argparse.ArgumentParser()
    a.add_argument("project")
    a = a.parse_args()
    print(slr_init(a.project))


if __name__ == "__main__":
    main()
```

`config.py`: tambah baris `SLR_DIR = os.environ.get("SLR_DIR", "./slr")` setelah `PAPERS_DIR`.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_slr.py -v`
Expected: PASS (1 passed)

- [ ] **Step 5: Commit**

```bash
git add slr_init.py config.py tests/test_slr.py
git commit -m "feat: slr_init buat proyek + protocol.json template"
```

---

### Task 2: `grabbers.py` + `ieee_grab.py` dukung `--source`

**Files:**
- Create: `grabbers.py`
- Modify: `ieee_grab.py` (tambah arg `--source` default `ieee`, out jadi `papers/<source>` bila `-o` tak diberi)
- Test: `tests/test_slr.py` (tambah test)

**Interfaces:**
- Consumes: —
- Produces: `detect_source(url_or_query: str) -> str` ("ieee"|"scopus"|"other"); dipakai `screen.py`/`report.py` untuk kolom `source`.

- [ ] **Step 1: Write the failing test**

```python
from grabbers import detect_source


def test_detect_source():
    assert detect_source("https://ieeexplore.ieee.org/search/searchresult.jsp?queryText=x") == "ieee"
    assert detect_source("https://www.scopus.com/results/results.uri?sort=plf-f") == "scopus"
    assert detect_source("some raw query string") == "other"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_slr.py::test_detect_source -v`
Expected: FAIL ("No module named 'grabbers'")

- [ ] **Step 3: Write minimal implementation**

`grabbers.py`:

```python
"""Deteksi sumber paper dari link + base class grabber per sumber."""
import urllib.parse


def detect_source(url_or_query):
    """Return 'ieee' | 'scopus' | 'other'."""
    if not url_or_query.startswith("http"):
        return "other"
    netloc = urllib.parse.urlparse(url_or_query).netloc
    if "ieeexplore" in netloc:
        return "ieee"
    if "scopus" in netloc:
        return "scopus"
    return "other"


class BaseGrabber:
    """Interface grabber per sumber. Subclass override run()."""

    source = "other"

    def run(self, query_or_url, out, max_n=0, delay=2.0):
        raise NotImplementedError
```

`ieee_grab.py`: tambah argumen (setelah `-o`):

```python
a.add_argument("--source", default="ieee")
```

dan sebelum `os.makedirs`, tambah:

```python
    if a.out == "papers":
        a.out = f"papers/{detect_source(a.query_or_url) if a.source == 'ieee' else a.source}"
```

dengan import `from grabbers import detect_source` di atas. Perilaku: default `-o papers` + link IEEE → `papers/ieee/`; `-o` eksplisit dihormati apa adanya.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_slr.py -v`
Expected: PASS (semua test lolos)

- [ ] **Step 5: Commit**

```bash
git add grabbers.py ieee_grab.py tests/test_slr.py
git commit -m "feat: detect_source + ieee_grab --source ke papers/<source>"
```

---

### Task 3: `screen.py` screening semi-otomatis

**Files:**
- Create: `screen.py`
- Test: `tests/test_slr.py` (tambah test)

**Interfaces:**
- Consumes: `slr_init()` path layout (Task 1), `grabbers.detect_source()` (Task 2), `llm.chat()` return `(text, via)`, `config.PAPERS_DIR`
- Produces: `decisions.csv` kolom `file,source,phase,decision,reason,qa_score`; dipakai Task 4-5.

- [ ] **Step 1: Write the failing test**

```python
import csv


def test_screen_auto_include(tmp_path, monkeypatch):
    from screen import score_paper
    monkeypatch.setattr("screen.llm", _FakeLLM())
    s = score_paper("Test Title", "Test abstract about trust.", ["RQ1?"], ["English"], ["Non-English"])
    assert 0 <= s["score"] <= 100
    assert s["reason"]
```

dengan helper di atas file test:

```python
class _FakeLLM:
    def chat(self, messages):
        import json
        return json.dumps({"score": 90, "reason": "relevan"}), "fake"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_slr.py::test_screen_auto_include -v`
Expected: FAIL ("No module named 'screen'")

- [ ] **Step 3: Write minimal implementation**

```python
#!/usr/bin/env python3
"""Screening semi-otomatis: LLM skor judul+abstrak, user putuskan y/n.

Tulis slr/<project>/decisions.csv (file,source,phase,decision,reason,qa_score).
Dedup via DOI/judul sebelum screening.

Pakai:  .venv/bin/python screen.py <project> [--phase title_abstract|fulltext] [--auto --min-score 80]
"""
import argparse
import csv
import json
import os

from pypdf import PdfReader

import config
import llm
from grabbers import detect_source

DECISION_FIELDS = ["file", "source", "phase", "decision", "reason", "qa_score"]

SCORE_PROMPT = """Kamu reviewer SLR. Nilai relevansi paper ini 0-100.
RQ: {rq}
Inklusi: {inc}
Eksklusi: {exc}
Judul: {title}
Abstrak: {abstract}
Jawab JSON saja: {{"score": N, "reason": "1 kalimat"}}"""


def score_paper(title, abstract, rq, inc, exc):
    raw, _ = llm.chat([{"role": "user", "content": SCORE_PROMPT.format(
        rq=rq, inc=inc, exc=exc, title=title, abstract=abstract[:2000])}])
    d = json.loads(raw[raw.find("{"):raw.rfind("}") + 1])
    return {"score": max(0, min(100, int(d["score"]))), "reason": d.get("reason", "")}


def full_text_of(path):
    r = PdfReader(path)
    return "\n".join((p.extract_text() or "") for p in r.pages)


def main():
    a = argparse.ArgumentParser()
    a.add_argument("project")
    a.add_argument("--phase", choices=["title_abstract", "fulltext"], default="title_abstract")
    a.add_argument("--auto", action="store_true")
    a.add_argument("--min-score", type=int, default=80)
    a = a.parse_args()

    proj = f"{config.SLR_DIR}/{a.project}"
    proto = json.load(open(f"{proj}/protocol.json"))
    dec_path = f"{proj}/decisions.csv"
    seen = set()
    if os.path.exists(dec_path):
        with open(dec_path) as f:
            seen = {(r["file"], r["phase"]) for r in csv.DictReader(f)}

    files = sorted(f for f in os.listdir(config.PAPERS_DIR) if f.endswith(".pdf"))
    if a.phase == "fulltext":
        passed = {r["file"] for r in csv.DictReader(open(dec_path))
                  if r["phase"] == "title_abstract" and r["decision"] == "include"}
        files = [f for f in files if f in passed]
    files = [f for f in files if (f, a.phase) not in seen]  # seen berisi tuple (file, phase)
    with open(dec_path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=DECISION_FIELDS)
        if not seen:
            w.writeheader()
        for pdf in files:
            text = full_text_of(f"{config.PAPERS_DIR}/{pdf}")
            if a.phase == "title_abstract":
                text = "\n".join(text.split("\n")[:60])
            s = score_paper(text.split("\n")[0][:200], text,
                            proto["research_questions"], proto["inclusion"], proto["exclusion"])
            if a.auto and s["score"] >= a.min_score:
                dec = "include"
            else:
                print(f"\n{pdf}\nskor={s['score']} {s['reason']}")
                dec = "include" if input("include? [y/N] ").lower() == "y" else "exclude"
            w.writerow({"file": pdf, "source": detect_source(pdf),
                        "phase": a.phase, "decision": dec,
                        "reason": s["reason"], "qa_score": ""})
            print(f"{dec}: {pdf}")


if __name__ == "__main__":
    main()
```

Catatan: `source` dari nama file = "other" bila file lokal tanpa URL. Untuk grab baru, `ieee_grab.py` catat sumber via folder `papers/<source>/`; `screen.py` baca folder `papers/*/` rekursif bila ada subfolder (implementasi: jalan `os.walk`, `source` = nama subfolder bila ada, else `detect_source`). Sederhanakan: gunakan `os.walk` + source dari nama parent dir.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_slr.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add screen.py tests/test_slr.py
git commit -m "feat: screen.py screening semi-otomatis + decisions.csv"
```

---

### Task 4: `report.py` PRISMA SVG + tabel + BibTeX

**Files:**
- Create: `report.py`
- Test: `tests/test_slr.py` (tambah test)

**Interfaces:**
- Consumes: `decisions.csv` (Task 3), `literature.csv`/`extraction.csv` kolom
- Produces: `slr/<project>/prisma.svg`, `slr/<project>/report.md`, reuse `export_bib.py` untuk `references.bib`.

- [ ] **Step 1: Write the failing test**

```python
def test_report_counts(tmp_path):
    from report import prisma_counts
    rows = [
        {"file": "a.pdf", "source": "ieee", "phase": "title_abstract", "decision": "include", "reason": "", "qa_score": ""},
        {"file": "b.pdf", "source": "ieee", "phase": "title_abstract", "decision": "exclude", "reason": "off-topic", "qa_score": ""},
        {"file": "a.pdf", "source": "ieee", "phase": "fulltext", "decision": "include", "reason": "", "qa_score": "3"},
    ]
    c = prisma_counts(rows)
    assert c["identified_ieee"] == 2
    assert c["excluded_title_abstract"] == 1
    assert c["included"] == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_slr.py::test_report_counts -v`
Expected: FAIL ("No module named 'report'")

- [ ] **Step 3: Write minimal implementation**

```python
#!/usr/bin/env python3
"""Laporan SLR: decisions.csv -> prisma.svg + report.md.

Pakai:  .venv/bin/python report.py <project>
"""
import argparse
import csv
from collections import Counter

import config

BOX_W, BOX_H, GAP = 320, 54, 18


def prisma_counts(rows):
    """Hitung angka PRISMA dari decisions.csv rows."""
    ident = Counter(r["source"] for r in rows if r["phase"] == "title_abstract")
    ta_ex = sum(1 for r in rows if r["phase"] == "title_abstract" and r["decision"] == "exclude")
    ft = [r for r in rows if r["phase"] == "fulltext"]
    ft_ex = sum(1 for r in ft if r["decision"] == "exclude")
    reasons = Counter(r["reason"] for r in ft if r["decision"] == "exclude" and r["reason"])
    return {
        "by_source": dict(ident),
        "identified_total": sum(ident.values()),
        "excluded_title_abstract": ta_ex,
        "assessed_fulltext": len(ft),
        "excluded_fulltext": ft_ex,
        "excluded_reasons": dict(reasons),
        "included": sum(1 for r in ft if r["decision"] == "include"),
    }


def prisma_svg(c):
    """Render diagram alir PRISMA sederhana (kotak + panah vertikal), stdlib."""
    boxes = [
        f"Identification: {c['identified_total']} records "
        + ", ".join(f"{k}={v}" for k, v in c["by_source"].items()),
        f"Title/abstract screened, excluded {c['excluded_title_abstract']}",
        f"Full-text assessed: {c['assessed_fulltext']}, excluded {c['excluded_fulltext']}",
        f"Included: {c['included']}",
    ]
    h = len(boxes) * (BOX_H + GAP) + GAP
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{BOX_W + 40}" height="{h}">']
    y = GAP
    for i, b in enumerate(boxes):
        parts.append(f'<rect x="20" y="{y}" width="{BOX_W}" height="{BOX_H}" fill="white" stroke="black"/>'
                     f'<text x="30" y="{y + 30}" font-size="13">{b[:52]}</text>')
        if i:
            parts.append(f'<line x1="{20 + BOX_W // 2}" y1="{y - GAP}" x2="{20 + BOX_W // 2}" y2="{y}" stroke="black"/>'
                         '<polygon points="0,0" fill="black"/>')
        y += BOX_H + GAP
    parts.append("</svg>")
    return "\n".join(parts).replace('<polygon points="0,0" fill="black"/>',
                                    f'<polygon points="{20 + BOX_W // 2 - 5},{y - BOX_H - GAP} '
                                    f'{20 + BOX_W // 2 + 5},{y - BOX_H - GAP} '
                                    f'{20 + BOX_W // 2},{y - BOX_H - GAP + 8}" fill="black"/>')


def main():
    a = argparse.ArgumentParser()
    a.add_argument("project")
    a = a.parse_args()
    proj = f"{config.SLR_DIR}/{a.project}"
    rows = list(csv.DictReader(open(f"{proj}/decisions.csv")))
    c = prisma_counts(rows)
    open(f"{proj}/prisma.svg", "w").write(prisma_svg(c))
    with open(f"{proj}/report.md", "w") as f:
        f.write(f"# Laporan SLR: {a.project}\n\nIdentified: {c['identified_total']} "
                f"({c['by_source']})\n\nExcluded title/abstract: {c['excluded_title_abstract']}\n\n"
                f"Full-text: {c['assessed_fulltext']}, excluded: {c['excluded_fulltext']} "
                f"{c['excluded_reasons']}\n\n**Included: {c['included']}**\n")
    print(f"OK {proj}/prisma.svg {proj}/report.md")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_slr.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add report.py tests/test_slr.py
git commit -m "feat: report.py hitungan PRISMA + SVG + report.md"
```

---

### Task 5: Integrasi + `.gitignore` + smoke test end-to-end

**Files:**
- Modify: `.gitignore` (tambah `slr/`, `tests/__pycache__/`, jaga `docs/slr-design.md` ter-commit)
- Modify: `requirements.txt` (tambah `pytest`)
- Test: smoke manual (bukan pytest): init → screen 1 file dummy → extract → report, dengan 1 PDF copy ke `/tmp/papers_smoke` + `PAPERS_DIR` override env.

**Interfaces:**
- Consumes: Task 1-4
- Produces: repo siap dipakai; `docs/slr-design.md` tetap acuan.

- [ ] **Step 1: Tulis skenario smoke (bukan test file, langkah manual)**

```bash
mkdir -p /tmp/papers_smoke && cp "papers/$(ls papers | head -1)" /tmp/papers_smoke/
PAPERS_DIR=/tmp/papers_smoke .venv/bin/python slr_init.py smoke
# isi RQ/IC/EC di slr/smoke/protocol.json secara manual (2 baris contoh)
printf 'y\n' | PAPERS_DIR=/tmp/papers_smoke .venv/bin/python screen.py smoke
PAPERS_DIR=/tmp/papers_smoke .venv/bin/python extract.py smoke
PAPERS_DIR=/tmp/papers_smoke .venv/bin/python report.py smoke
PAPERS_DIR=/tmp/papers_smoke .venv/bin/python gaps.py smoke
ls slr/smoke/  # harus ada: protocol.json decisions.csv extraction.csv gaps.md prisma.svg report.md
```

- [ ] **Step 2: Jalankan smoke, verifikasi gagal**

Expected saat ini: GAGAL di `screen.py` bila LLM butuh API key — set `OPENROUTER_API_KEY` dari `.env` (sudah ada). Bila gagal lain, catat error.

- [ ] **Step 3: Perbaiki minimal agar smoke lolos**

Hanya fix yang dibutuhkan smoke (import, path). Tanpa refaktor.

- [ ] **Step 4: Jalankan ulang smoke sampai lolos**

Expected: 4 file ada di `slr/smoke/`, lalu `rm -rf slr/smoke /tmp/papers_smoke`.

- [ ] **Step 5: Commit**

```bash
git add .gitignore requirements.txt
git commit -m "chore: slr smoke test lolos, ignore slr/ + pytest dep"
```
