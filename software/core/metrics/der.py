"""
DER (Diarization Error Rate) — метрика качества диаризации (E2.1, EPIC-2).

Кадровая реализация (шаг 10 мс) без внешних зависимостей:
DER = (missed + false_alarm + confusion) / total_reference_speech.
Сопоставление меток спикеров ref<->hyp — жадное по пересечению во времени
(упрощение относительно оптимального венгерского алгоритма; для наших
1-4 спикеров расхождение незначимо, зафиксировано здесь осознанно).

Вход: списки (start_sec, end_sec, speaker_label).
"""
from dataclasses import dataclass

FRAME = 0.01  # 10 мс

Turn = tuple[float, float, str]


def _frames(turns: list[Turn], n_frames: int) -> list[str | None]:
    tl: list[str | None] = [None] * n_frames
    for start, end, spk in turns:
        for i in range(int(round(start / FRAME)), min(int(round(end / FRAME)), n_frames)):
            tl[i] = spk
    return tl


@dataclass
class DerResult:
    der: float
    missed: float
    false_alarm: float
    confusion: float
    total_speech: float


def der(reference: list[Turn], hypothesis: list[Turn]) -> DerResult:
    if not reference:
        raise ValueError("эталонная разметка пуста")
    horizon = max(end for _, end, _ in reference + hypothesis or reference)
    n = int(round(horizon / FRAME)) + 1
    ref, hyp = _frames(reference, n), _frames(hypothesis, n)

    # Жадное сопоставление меток по времени совместной речи.
    overlap: dict[tuple[str, str], int] = {}
    for r, h in zip(ref, hyp, strict=True):
        if r is not None and h is not None:
            overlap[(r, h)] = overlap.get((r, h), 0) + 1
    mapping: dict[str, str] = {}
    used_ref: set[str] = set()
    for (r, h), _cnt in sorted(overlap.items(), key=lambda kv: -kv[1]):
        if h not in mapping and r not in used_ref:
            mapping[h] = r
            used_ref.add(r)

    miss = fa = conf = total = 0
    for r, h in zip(ref, hyp, strict=True):
        if r is not None:
            total += 1
        if r is not None and h is None:
            miss += 1
        elif r is None and h is not None:
            fa += 1
        elif r is not None and h is not None and mapping.get(h) != r:
            conf += 1
    if total == 0:
        raise ValueError("в эталоне нет речи")
    return DerResult(
        der=(miss + fa + conf) / total,
        missed=miss * FRAME,
        false_alarm=fa * FRAME,
        confusion=conf * FRAME,
        total_speech=total * FRAME,
    )
