from __future__ import annotations

from typing import Any

from libs.common.config import get_settings
from libs.llm.base import BaseStructuredChatModel
from libs.llm.ollama_client import OllamaClient


class OllamaStructuredChatModel(BaseStructuredChatModel):
    provider_name = "ollama"

    def __init__(self, *, model_name: str | None = None, base_url: str | None = None) -> None:
        settings = get_settings()
        super().__init__(model_name=model_name or settings.chat_model)
        self.client = OllamaClient(base_url=base_url)

    def chat_json(self, *, system_prompt: str, user_prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        return self.client.chat_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema=schema,
            model=self.model_name,
        )
