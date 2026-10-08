import io
import json

from grabbers import detect_source

def test_bibtex_helpers():
    from bibtex import keywords, key
    assert keywords("2021_123_A Study of Graph Neural Networks for Traffic.pdf") == "study graph neural networks traffic"
    assert key("Ada Lovelace and Alan Turing", "2021", "A Study") == "Lovelace2021A"

def test_crossref_lookup(monkeypatch):
    import crossref
    item = {"DOI": "10.1/x", "title": ["Graph neural networks for traffic"], "author": [{"given": "Ada", "family": "Lovelace"}],
            "container-title": ["J"], "published": {"date-parts": [[2021]]}, "URL": "http://x"}
    body = {"message": {"items": [item]}}
    monkeypatch.setattr(crossref.urllib.request, "urlopen", lambda *a, **k: io.StringIO(json.dumps(body)))
    m = crossref.lookup("graph neural networks traffic", 2021)
    assert m and m["doi"] == "10.1/x" and m["authors"] == "Ada Lovelace"
    assert crossref.lookup("judul lain sekali xyzabc", 2021) is None

def test_detect_source():
    assert detect_source("https://ieeexplore.ieee.org/search/searchresult.jsp?queryText=x") == "ieee"
    assert detect_source("https://www.scopus.com/results/results.uri?sort=plf-f") == "scopus"
    assert detect_source("some raw query string") == "other"
    assert detect_source("https://openalex.org/works?search=x") == "openalex"

def test_openalex_params():
    from openalex_grab import build_params, pdf_urls, fname
    p = build_params("https://openalex.org/works?search=trust&filter=from_publication_date%3A2021-01-01")
    assert p["search"] == "trust" and "is_oa" in p["filter"]
    q = build_params("raw query")
    assert q["search"] == "raw query" and q["filter"] == "is_oa:true"
    w = {"id": "https://openalex.org/W1", "publication_year": 2021, "display_name": "T!",
         "best_oa_location": {"pdf_url": "http://a.pdf"},
         "locations": [{"is_oa": True, "pdf_url": "http://b.pdf"}]}
    assert pdf_urls(w) == ["http://a.pdf", "http://b.pdf"]
    assert fname(w).startswith("2021_W1_")
