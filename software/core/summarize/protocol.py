"""
Протокол встречи из стенограммы (E3.1/E3.2, EPIC-3): русские промпты, структурный
JSON-выход (решения, поручения с исполнителем/сроком), устойчивый парсинг.

Схема результата намеренно проще Meetily SummaryResponse: наш протокол — это
резюме + решения + поручения + ключевые моменты (см. docs/concept/scenarios.md,
«После встречи»). Расширение блоков — по обратной связи пилотов (EPIC-8).
"""
import json
import re
from dataclasses import asdict, dataclass, field

from core.summarize.llm import LLMBackend

SYSTEM_PROMPT = (
    "Ты — секретарь деловой встречи. Отвечай ТОЛЬКО валидным JSON без пояснений, "
    "строго по схеме: {\"meeting_name\": str, \"summary\": str, "
    "\"decisions\": [str], "
    "\"action_items\": [{\"assignee\": str, \"task\": str, \"due\": str|null}], "
    "\"key_points\": [str]}. Пиши по-русски, кратко и по существу. "
    "Если данных для поля нет — пустая строка/список, ничего не выдумывай."
)

USER_PROMPT = (
    "Составь протокол по стенограмме встречи. Реплики помечены спикерами.\n"
    "СТЕНОГРАММА:\n{transcript}"
)

CHUNK_CHARS = 24000  # ~6-8k токенов; крупные встречи режем с перекрытием
CHUNK_OVERLAP = 2000


@dataclass
class ActionItem:
    assignee: str
    task: str
    due: str | None = None


@dataclass
class Protocol:
    meeting_name: str = ""
    summary: str = ""
    decisions: list[str] = field(default_factory=list)
    action_items: list[ActionItem] = field(default_factory=list)
    key_points: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def parse_llm_json(raw: str) -> Protocol:
    """Устойчивый парсинг: срезает кодовые заборы, берёт внешний JSON-объект."""
    text = _FENCE.sub("", raw.strip())
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"в ответе LLM нет JSON-объекта: {raw[:120]!r}")
    data = json.loads(text[start : end + 1])
    return Protocol(
        meeting_name=str(data.get("meeting_name", "")),
        summary=str(data.get("summary", "")),
        decisions=[str(d) for d in data.get("decisions", []) or []],
        action_items=[
            ActionItem(
                assignee=str(a.get("assignee", "")),
                task=str(a.get("task", "")),
                due=(str(a["due"]) if a.get("due") else None),
            )
            for a in data.get("action_items", []) or []
            if isinstance(a, dict)
        ],
        key_points=[str(k) for k in data.get("key_points", []) or []],
    )


def _chunks(text: str) -> list[str]:
    if len(text) <= CHUNK_CHARS:
        return [text]
    step = CHUNK_CHARS - CHUNK_OVERLAP
    return [text[i : i + CHUNK_CHARS] for i in range(0, len(text), step)]


def _merge(parts: list[Protocol]) -> Protocol:
    if len(parts) == 1:
        return parts[0]
    merged = Protocol(meeting_name=next((p.meeting_name for p in parts if p.meeting_name), ""))
    merged.summary = " ".join(p.summary for p in parts if p.summary)
    for p in parts:
        merged.decisions += p.decisions
        merged.action_items += p.action_items
        merged.key_points += p.key_points
    return merged


def summarize_transcript(segments: list[dict], backend: LLMBackend) -> Protocol:
    """Сегменты стенограммы (dict из storage) -> протокол встречи."""
    lines = [
        f"[{s.get('speaker') or 'Говорящий ?'}] {s['text']}" for s in segments if s.get("text")
    ]
    if not lines:
        raise ValueError("стенограмма пуста — нечего резюмировать")
    text = "\n".join(lines)
    parts = [
        parse_llm_json(backend.complete(SYSTEM_PROMPT, USER_PROMPT.format(transcript=chunk)))
        for chunk in _chunks(text)
    ]
    return _merge(parts)
