"""Тесты смыслового слоя (EPIC-3): LLM-клиенты (MockTransport), парсинг протокола,
talk-time, Markdown-экспорт."""

import json

import httpx
import pytest

from core.analytics.talk_time import talk_time
from core.export.markdown import protocol_to_markdown
from core.summarize.llm import OllamaChat, OpenAICompatible
from core.summarize.protocol import (
    ActionItem,
    Protocol,
    parse_llm_json,
    summarize_transcript,
)

PROTOCOL_JSON = {
    "meeting_name": "Синк по пилоту",
    "summary": "Обсудили сроки пилота.",
    "decisions": ["Пилот стартует в сентябре"],
    "action_items": [{"assignee": "Анна", "task": "Подготовить договор", "due": "2026-08-01"}],
    "key_points": ["Бюджет утверждён"],
}

SEGMENTS = [
    {"start": 0.0, "end": 10.0, "text": "Начнём. Предлагаю старт в сентябре.", "speaker": "Анна"},
    {"start": 10.0, "end": 14.0, "text": "Согласен.", "speaker": "Борис"},
    {"start": 14.0, "end": 20.0, "text": "Договор за мной.", "speaker": "Анна"},
]


class StubLLM:
    def __init__(self, payload=None):
        self.calls: list[tuple[str, str]] = []
        self.payload = payload or PROTOCOL_JSON

    def complete(self, system, user):
        self.calls.append((system, user))
        return json.dumps(self.payload, ensure_ascii=False)


def test_summarize_builds_protocol_with_speakers_in_prompt():
    llm = StubLLM()
    p = summarize_transcript(SEGMENTS, llm)
    assert p.meeting_name == "Синк по пилоту"
    assert p.action_items == [
        ActionItem(assignee="Анна", task="Подготовить договор", due="2026-08-01")
    ]
    (system, user) = llm.calls[0]
    assert "[Анна]" in user and "[Борис]" in user  # спикеры дошли до промпта
    assert "JSON" in system


def test_empty_transcript_raises():
    with pytest.raises(ValueError):
        summarize_transcript([], StubLLM())


def test_parse_llm_json_with_fences_and_noise():
    raw = "Вот протокол:\n```json\n" + json.dumps(PROTOCOL_JSON, ensure_ascii=False) + "\n```"
    p = parse_llm_json(raw)
    assert p.decisions == ["Пилот стартует в сентябре"]


def test_parse_llm_json_garbage_raises():
    with pytest.raises(ValueError):
        parse_llm_json("никакого джейсона тут нет")


def test_ollama_client_contract():
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.read())
        assert request.url.path == "/api/chat"
        assert body["stream"] is False and body["format"] == "json"
        assert body["messages"][0]["role"] == "system"
        return httpx.Response(200, json={"message": {"content": "{\"summary\": \"ок\"}"}})

    c = OllamaChat(host="http://o", model="m", transport=httpx.MockTransport(handler))
    assert "ок" in c.complete("s", "u")


def test_openai_compatible_contract():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/chat/completions"
        assert request.headers["authorization"] == "Bearer k"
        return httpx.Response(
            200, json={"choices": [{"message": {"content": "{\"summary\": \"ок\"}"}}]}
        )

    c = OpenAICompatible(
        base_url="http://x", api_key="k", model="m", transport=httpx.MockTransport(handler)
    )
    assert "ок" in c.complete("s", "u")


def test_talk_time_shares():
    t = talk_time(SEGMENTS)
    assert t["total_seconds"] == pytest.approx(20.0)
    assert t["speakers"]["Анна"]["seconds"] == pytest.approx(16.0)
    assert t["speakers"]["Анна"]["share"] == pytest.approx(0.8)
    assert list(t["speakers"]) == ["Анна", "Борис"]  # сортировка по убыванию


def test_markdown_export_contains_all_blocks():
    p = Protocol(
        meeting_name="Синк",
        summary="Резюме.",
        decisions=["Решение 1"],
        action_items=[ActionItem("Анна", "Договор", "2026-08-01")],
        key_points=["Момент"],
    )
    md = protocol_to_markdown(p, talk_time(SEGMENTS))
    for token in (
        "# Протокол: Синк",
        "## Решения",
        "| Анна | Договор | 2026-08-01 |",
        "## Ключевые моменты",
        "## Время в разговоре",
    ):
        assert token in md
