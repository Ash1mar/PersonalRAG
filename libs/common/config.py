from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel


class Settings(BaseModel):
    chat_provider: str = "ollama"
    chat_model: str = "qwen2.5-coder:7b"
    embedding_provider: str = "ollama"
    embedding_model: str = "qwen2.5-coder:7b"
    retrieval_backends: list[str]
    ollama_base_url: str = "http://localhost:11434"
    ollama_timeout_seconds: int = 120
    local_kb_dir: Path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    workspace_dir = Path.cwd()
    default_kb_dir = workspace_dir / "data" / "local_kb"
    default_chat_model = os.getenv("PKB_CHAT_MODEL", os.getenv("PKB_OLLAMA_CHAT_MODEL", "qwen2.5-coder:7b"))
    default_embed_model = os.getenv("PKB_EMBEDDING_MODEL", os.getenv("PKB_OLLAMA_EMBED_MODEL", default_chat_model))
    retrieval_backends_raw = os.getenv("PKB_RETRIEVAL_BACKENDS", "local_vector")
    retrieval_backends = [item.strip() for item in retrieval_backends_raw.split(",") if item.strip()]
    return Settings(
        chat_provider=os.getenv("PKB_CHAT_PROVIDER", "ollama"),
        chat_model=default_chat_model,
        embedding_provider=os.getenv("PKB_EMBEDDING_PROVIDER", "ollama"),
        embedding_model=default_embed_model,
        retrieval_backends=retrieval_backends or ["local_vector"],
        ollama_base_url=os.getenv("PKB_OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/"),
        ollama_timeout_seconds=int(os.getenv("PKB_OLLAMA_TIMEOUT_SECONDS", "120")),
        local_kb_dir=Path(os.getenv("PKB_LOCAL_KB_DIR", str(default_kb_dir))),
    )
