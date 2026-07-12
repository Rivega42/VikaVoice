"""Аналитика встречи по сегментам стенограммы (E3.2): talk-time по спикерам."""


def talk_time(segments: list[dict]) -> dict:
    """{"speakers": {имя: {"seconds": s, "share": 0..1}}, "total_seconds": s}."""
    per: dict[str, float] = {}
    for s in segments:
        dur = max(0.0, float(s.get("end", 0)) - float(s.get("start", 0)))
        spk = s.get("speaker") or "Говорящий ?"
        per[spk] = per.get(spk, 0.0) + dur
    total = sum(per.values())
    return {
        "speakers": {
            spk: {"seconds": round(sec, 1), "share": round(sec / total, 3) if total else 0.0}
            for spk, sec in sorted(per.items(), key=lambda kv: -kv[1])
        },
        "total_seconds": round(total, 1),
    }
