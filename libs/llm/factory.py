from __future__ import annotations

from libs.common.config import get_settings
from libs.llm.base import BaseStructuredChatModel
from libs.llm.ollama_provider import OllamaStructuredChatModel


def get_chat_model_provider(provider_name: str | None = None, model_name: str | None = None) -> BaseStructuredChatModel:
    settings = get_settings()
    resolved_provider = provider_name or settings.chat_provider
    resolved_model = model_name or settings.chat_model
    if resolved_provider == "ollama":
        return OllamaStructuredChatModel(model_name=resolved_model)
    raise ValueError(f"Unsupported chat provider: {resolved_provider}")
