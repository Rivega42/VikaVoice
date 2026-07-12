"""Экспорт протокола встречи в Markdown (E3.3). Telegram/Notion — после EPIC-5/8."""

from core.summarize.protocol import Protocol


def protocol_to_markdown(p: Protocol, analytics: dict | None = None) -> str:
    lines = [f"# Протокол: {p.meeting_name or 'встреча'}", ""]
    if p.summary:
        lines += ["## Резюме", "", p.summary, ""]
    if p.decisions:
        lines += ["## Решения", ""] + [f"- {d}" for d in p.decisions] + [""]
    if p.action_items:
        lines += ["## Поручения", "", "| Исполнитель | Задача | Срок |", "|---|---|---|"]
        lines += [
            f"| {a.assignee or '—'} | {a.task} | {a.due or '—'} |" for a in p.action_items
        ]
        lines.append("")
    if p.key_points:
        lines += ["## Ключевые моменты", ""] + [f"- {k}" for k in p.key_points] + [""]
    if analytics and analytics.get("speakers"):
        lines += ["## Время в разговоре", ""]
        lines += [
            f"- {spk}: {v['seconds']} с ({v['share']:.0%})"
            for spk, v in analytics["speakers"].items()
        ]
        lines.append("")
    return "\n".join(lines)
