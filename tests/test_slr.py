import json
import shutil
import subprocess
import sys

from grabbers import detect_source

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


def test_detect_source():
    assert detect_source("https://ieeexplore.ieee.org/search/searchresult.jsp?queryText=x") == "ieee"
    assert detect_source("https://www.scopus.com/results/results.uri?sort=plf-f") == "scopus"
    assert detect_source("some raw query string") == "other"


class _FakeLLM:
    def chat(self, messages):
        import json as _j
        return _j.dumps({"score": 90, "reason": "relevan"}), "fake"


def test_screen_scores(monkeypatch):
    from screen import score_paper
    monkeypatch.setattr("screen.llm", _FakeLLM())
    s = score_paper("Test Title", "Test abstract about trust.", ["RQ1?"], ["English"], ["Non-English"])
    assert 0 <= s["score"] <= 100
    assert s["reason"]


def test_report_counts():
    from report import prisma_counts
    rows = [
        {"file": "a.pdf", "source": "ieee", "phase": "title_abstract", "decision": "include", "reason": "", "qa_score": ""},
        {"file": "b.pdf", "source": "ieee", "phase": "title_abstract", "decision": "exclude", "reason": "off-topic", "qa_score": ""},
        {"file": "a.pdf", "source": "ieee", "phase": "fulltext", "decision": "include", "reason": "", "qa_score": "3"},
    ]
    c = prisma_counts(rows)
    assert c["by_source"]["ieee"] == 2
    assert c["excluded_title_abstract"] == 1
    assert c["included"] == 1


class _FakeLLM_QA:
    def chat(self, messages):
        import json as _j
        prompt = messages[0]["content"]
        if prompt.startswith("QA:"):
            return _j.dumps({"qa1": 1}), "fake"
        return _j.dumps({"answers_rq1": "jawaban 1", "answers_rq2": "jawaban 2"}), "fake"


def test_extract_qa(monkeypatch):
    from extract import answer_rq, score_qa
    monkeypatch.setattr("extract.llm", _FakeLLM_QA())
    a = answer_rq("full text ...", ["RQ1?", "RQ2?"])
    assert set(a) == {"answers_rq1", "answers_rq2"}
    assert all(a.values())
    s = score_qa("full text ...", [{"id": "qa1", "question": "Q?", "weight": 2}])
    assert s == 2


class _FakeLLM_Gaps:
    def chat(self, messages):
        return ("## Research Gaps\n\n| Gap | Bukti | Kandidat RQ |\n"
                "|---|---|---|\n"
                "| metode X jenuh di trust | a.pdf, b.pdf | RQ baru: di luar trust? |\n"), "fake"


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
