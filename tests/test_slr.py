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
