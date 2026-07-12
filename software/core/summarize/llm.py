"""
Подключаемый LLM-бэкенд для смыслового слоя (E3.1, EPIC-3) — симметрично ASRBackend.

Реализации:
  OllamaChat        -> локальный Ollama /api/chat (Edge/On-prem, офлайн)
  OpenAICompatible  -> любой OpenAI-совместимый endpoint (OCPlatform, облако);
                       ключ/URL приходят из конфига, в коде и репозитории их НЕТ.

Оба возвращают сырой текст ответа модели; парсинг JSON-протокола — protocol.py.
Подход адаптирован из вендоренного Meetily transcript_processor.py (MIT),
но без pydantic_ai: нам достаточно httpx + строгий промпт со схемой.
"""
from abc import ABC, abstractmethod

import httpx


class LLMBackend(ABC):
    @abstractmethod
    def complete(self, system: str, user: str) -> str: ...


class OllamaChat(LLMBackend):
    def __init__(
        self,
        host: str = "http://localhost:11434",
        model: str = "qwen2.5:3b",
        timeout: float = 600.0,
        transport: httpx.BaseTransport | None = None,
    ):
        self.host, self.model = host.rstrip("/"), model
        self._client = httpx.Client(timeout=timeout, transport=transport)

    def complete(self, system: str, user: str) -> str:
        r = self._client.post(
            f"{self.host}/api/chat",
            json={
                "model": self.model,
                "stream": False,
                "format": "json",
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
        )
        r.raise_for_status()
        return r.json()["message"]["content"]


class OpenAICompatible(LLMBackend):
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        timeout: float = 600.0,
        transport: httpx.BaseTransport | None = None,
    ):
        self.base_url, self.model = base_url.rstrip("/"), model
        self._headers = {"Authorization": f"Bearer {api_key}"}
        self._client = httpx.Client(timeout=timeout, transport=transport)

    def complete(self, system: str, user: str) -> str:
        r = self._client.post(
            f"{self.base_url}/v1/chat/completions",
            headers=self._headers,
            json={
                "model": self.model,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
