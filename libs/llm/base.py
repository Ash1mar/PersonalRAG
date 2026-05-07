from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseStructuredChatModel(ABC):
    provider_name = "base"

    def __init__(self, *, model_name: str | None = None) -> None:
        self.model_name = model_name

    @property
    def backend_name(self) -> str:
        return f"{self.provider_name}:{self.model_name}" if self.model_name else self.provider_name

    @abstractmethod
    def chat_json(self, *, system_prompt: str, user_prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError
