"""HTTP client OpenRouter + fallback Ollama. Stdlib only."""
import json
import urllib.request

import config


def _post(url, payload, headers=None, timeout=120):
    req = urllib.request.Request(
        url, json.dumps(payload).encode(),
        {"Content-Type": "application/json", **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def embed(texts):
    """Embed via OpenRouter. Return list[list[float]]."""
    d = _post(f"https://openrouter.ai/api/v1/embeddings",
              {"model": config.OPENROUTER_EMBED_MODEL, "input": texts},
              {"Authorization": f"Bearer {config.OPENROUTER_API_KEY}"})
    return [e["embedding"] for e in d["data"]]


def chat_openrouter(messages):
    d = _post("https://openrouter.ai/api/v1/chat/completions",
              {"model": config.OPENROUTER_CHAT_MODEL, "messages": messages},
              {"Authorization": f"Bearer {config.OPENROUTER_API_KEY}"})
    return d["choices"][0]["message"]["content"]


def chat_ollama(messages):
    d = _post(f"{config.OLLAMA_URL}/api/chat",
              {"model": config.OLLAMA_MODEL, "messages": messages, "stream": False})
    return d["message"]["content"]


def chat(messages):
    """Chat via OpenRouter, fallback Ollama bila gagal."""
    try:
        return chat_openrouter(messages), "openrouter"
    except Exception as e:
        print(f"OpenRouter gagal ({e}), fallback Ollama...")
        return chat_ollama(messages), "ollama"
