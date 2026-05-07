from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from libs.common.config import get_settings


class OllamaClient:
    def __init__(self, base_url: str | None = None, timeout_seconds: int | None = None) -> None:
        settings = get_settings()
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.timeout_seconds = timeout_seconds or settings.ollama_timeout_seconds

    def chat_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        schema: dict[str, Any],
        model: str | None = None,
    ) -> dict[str, Any]:
        settings = get_settings()
        payload = {
            "model": model or settings.ollama_chat_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "format": schema,
            "options": {"temperature": 0},
        }
        response = self._post_json("/api/chat", payload)
        content = response["message"]["content"]
        return json.loads(content)

    def embed(self, texts: list[str], model: str | None = None) -> list[list[float]]:
        settings = get_settings()
        payload = {
            "model": model or settings.ollama_embed_model,
            "input": texts,
        }
        response = self._post_json("/api/embed", payload)
        return response["embeddings"]

    def tags(self) -> dict[str, Any]:
        request = urllib.request.Request(f"{self.base_url}/api/tags", method="GET")
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))

    def _post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Failed to call Ollama at {self.base_url}{path}: {exc}") from exc
