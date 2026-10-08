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

def test_project_paths_and_validation(monkeypatch):
    import pytest
    import config
    monkeypatch.setattr(config, "PROJECTS_DIR", "/tmp/x")
    p = config.Project("skripsi-a")
    assert p.papers == "/tmp/x/skripsi-a/papers" and p.chroma == "/tmp/x/skripsi-a/chroma"
    for bad in ("../etc", "a/b", "", ".hidden", "a" * 65):
        with pytest.raises(ValueError):
            config.Project(bad)

def test_project_ensure_isolated(tmp_path, monkeypatch):
    import config
    monkeypatch.setattr(config, "PROJECTS_DIR", str(tmp_path))
    config.Project("a").ensure(); config.Project("b").ensure()
    assert (tmp_path / "a/papers").is_dir() and (tmp_path / "b/papers").is_dir()

def test_scopus_helpers():
    from scopus_grab import scopus_query, entry_dois
    assert scopus_query("graph neural") == "(TITLE-ABS-KEY(graph neural)) AND OPENACCESS(1)"
    assert scopus_query("AUTHOR-NAME(Smith)") == "(AUTHOR-NAME(Smith)) AND OPENACCESS(1)"
    assert scopus_query("TITLE(x) AND OPENACCESS(1)") == "TITLE(x) AND OPENACCESS(1)"
    es = [{"prism:doi": "10.1/A"}, {"error": "Result set was empty"}, {"prism:doi": "10.1/b,c"}, {}]
    assert entry_dois(es) == ["10.1/a"]

def test_papermeta(tmp_path):
    import papermeta as pm
    w = {"display_name": "T", "publication_year": 2021, "doi": "https://doi.org/10.1/X",
         "authorships": [{"author": {"display_name": "Ada L"}}, {"author": {"display_name": "Alan T"}}],
         "abstract_inverted_index": {"hello": [0], "world": [1]}}
    m = pm.from_openalex(w)
    assert m["authors"] == "Ada L and Alan T" and m["doi"] == "10.1/X" and m["abstract"] == "hello world"
    assert pm.from_ieee({"articleTitle": "<b>A</b>", "publicationYear": "2024", "authors": [{"preferredName": "X Y"}]})["title"] == "A"
    assert pm.from_filename("2021_W9_Some Title.pdf")["year"] == 2021
    assert pm.from_filename("odd name.pdf")["title"] == "odd name"
    assert pm.find_doi("see https://doi.org/10.1109/ACCESS.2024.3446619.") == "10.1109/access.2024.3446619"
    assert pm.find_doi("no doi here") is None
    pdf = str(tmp_path / "a.pdf")
    pm.save(pdf, m)
    assert pm.resolve(pdf)["title"] == "T"  # sidecar menang, tanpa jaringan

def test_ingest_one_metadata_pages_batches(tmp_path, monkeypatch):
    import chromadb, config, ingest
    calls = []
    monkeypatch.setattr(ingest.llm, "embed", lambda ts: calls.append(len(ts)) or [[1.0, 0.0]] * len(ts))
    monkeypatch.setattr(config, "EMBED_BATCH", 2)
    col = chromadb.PersistentClient(path=str(tmp_path)).get_or_create_collection("papers")
    meta = {"title": "T", "authors": "A", "year": 2021, "doi": "10.1/x", "abstract": "abs"}
    n = ingest.ingest_one(col, "f.pdf", ["page one", "", "page three"], meta)
    assert n == 3 and calls == [2, 1]  # abstrak + 2 halaman berisi, batch 2
    got = col.get(include=["metadatas"])["metadatas"]
    assert sorted(m["page"] for m in got) == [0, 1, 3] and all(m["title"] == "T" and m["year"] == 2021 for m in got)

def test_ingest_failure_leaves_nothing(tmp_path, monkeypatch):
    import chromadb, ingest
    def boom(ts): raise RuntimeError("api")
    monkeypatch.setattr(ingest.llm, "embed", boom)
    col = chromadb.PersistentClient(path=str(tmp_path)).get_or_create_collection("papers")
    try:
        ingest.ingest_one(col, "f.pdf", ["x"], {})
    except RuntimeError:
        pass
    assert col.count() == 0

def test_store_guards_embed_model(tmp_path, monkeypatch):
    import pytest, config, store
    monkeypatch.setattr(config, "PROJECTS_DIR", str(tmp_path))
    p = config.Project("a").ensure()
    col = store.open_collection(p, create=True)
    col.add(ids=["1"], embeddings=[[1.0, 0.0]], documents=["x"])
    assert store.open_collection(p).count() == 1
    monkeypatch.setattr(config, "OPENROUTER_EMBED_MODEL", "model/lain")
    with pytest.raises(SystemExit):
        store.open_collection(p)
    assert store.open_collection(p, create=True, reset=True).count() == 0

def test_evidence_cite_and_select():
    import evidence as ev
    assert ev.cite({"authors": "Fupeng Wei and Xing Liu and L Pan", "year": 2025, "page": 6}) == "Wei dkk. 2025, hlm. 6"
    assert ev.cite({"authors": "Ada Lovelace and Alan Turing", "year": 2021, "page": 0}) == "Lovelace dan Turing 2021, abstrak"
    assert ev.cite({"authors": "", "year": 0, "page": 3, "title": "Judul X", "file": "f.pdf"}) == "Judul X t.t., hlm. 3"
    refs = "[3] Lo WW et al (2020) In: Proceedings of X, pp 1-9. [4] Kim 2019 vol. 3 [5] Lee 2018 [6] Roe 2017"
    assert ev.is_reference_list(refs) and not ev.is_reference_list("The model was trained in 2021 on data.")
    res = {"distances": [[0.2, 0.3, 0.35, 0.6]],
           "metadatas": [[{}, {}, {}, {}]], "documents": [["a", refs, "c", "d"]]}
    assert [t for _, _, t in ev.select(res, k=5, max_dist=0.4)] == ["a", "c"]  # daftar pustaka & jarak jauh keluar
    assert ev.select(res, k=1, max_dist=0.4)[0][2] == "a"
    assert ev.cited_ids("x [S1] y [S3] z [S9]", 3) == ([1, 3], [9])

def test_ask_refuses_without_evidence(tmp_path, monkeypatch):
    import json, config, rag, store
    monkeypatch.setattr(config, "PROJECTS_DIR", str(tmp_path))
    p = config.Project("a").ensure()
    col = store.open_collection(p, create=True)
    col.add(ids=["1"], embeddings=[[1.0, 0.0]], documents=["x"], metadatas=[{"file": "f", "page": 1, "title": "", "authors": "", "year": 0, "doi": ""}])
    monkeypatch.setattr(rag.llm, "embed", lambda ts: [[0.0, 1.0]])  # tegak lurus = jarak 1.0
    def no_chat(m): raise AssertionError("LLM tak boleh dipanggil tanpa bukti")
    monkeypatch.setattr(rag.llm, "chat", no_chat)
    r = rag.ask(p, "apa saja")
    assert r["status"] == "no_evidence" and r["evidence"] == []
    monkeypatch.setattr(rag.llm, "embed", lambda ts: [[1.0, 0.0]])
    monkeypatch.setattr(rag.llm, "chat", lambda m: ("Jawab [S1] dan [S4]", "fake"))
    r = rag.ask(p, "apa saja")
    assert r["status"] == "answered" and r["cited"] == [1] and r["invalid_cites"] == [4]
    log = [json.loads(l) for l in open(f"{p.dir}/decisions.jsonl")]
    assert [x["status"] for x in log] == ["no_evidence", "answered"] and log[1]["evidence"][0]["file"] == "f"
