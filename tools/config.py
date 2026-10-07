"""Config RAG: baca .env via stdlib."""
import os


def load_env(path=".env"):
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())


load_env()

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_EMBED_MODEL = os.environ.get("OPENROUTER_EMBED_MODEL", "qwen/qwen3-embedding-8b")
OPENROUTER_CHAT_MODEL = os.environ.get("OPENROUTER_CHAT_MODEL", "openai/gpt-4o-mini")
NINEROUTER_URL = os.environ.get("NINEROUTER_URL", "http://localhost:20128")
NINEROUTER_API_KEY = os.environ.get("NINEROUTER_API_KEY", "")
NINEROUTER_MODEL = os.environ.get("NINEROUTER_MODEL", "main")
LLM_BACKEND = os.environ.get("LLM_BACKEND", "openrouter")  # openrouter | ninerouter
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1")
CHROMA_DIR = os.environ.get("CHROMA_DIR", "./chroma_db")
PAPERS_DIR = os.environ.get("PAPERS_DIR", "./papers")
SLR_DIR = os.environ.get("SLR_DIR", "./slr")
COLLECTION = "papers"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
TOP_K = 5
