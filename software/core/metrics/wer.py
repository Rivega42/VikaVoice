"""
WER (Word Error Rate) для контроля качества ASR на русском (E1.5, EPIC-1).

Чистый Python без зависимостей: нормализация текста + расстояние Левенштейна
по словам. Используется скриптом оценки и тестами; baseline фиксируется
в docs/roadmap.md (E1.5) по мере появления эталонных записей.

CLI:  python -m core.metrics.wer <reference.txt> <hypothesis.txt>
"""
import re
import sys
from dataclasses import dataclass

_PUNCT = re.compile(r"[^\w\s]", flags=re.UNICODE)
_WS = re.compile(r"\s+")
_SPEAKER_PREFIX = re.compile(r"\(speaker [^)]*\)")


def normalize(text: str) -> list[str]:
    """Нижний регистр, ё->е, без пунктуации и служебных префиксов спикеров."""
    text = _SPEAKER_PREFIX.sub(" ", text.lower()).replace("ё", "е")
    text = _PUNCT.sub(" ", text)
    return [w for w in _WS.split(text) if w]


@dataclass
class WerResult:
    wer: float
    substitutions: int
    deletions: int
    insertions: int
    ref_words: int


def wer(reference: str, hypothesis: str) -> WerResult:
    ref, hyp = normalize(reference), normalize(hypothesis)
    if not ref:
        raise ValueError("эталонный текст пуст после нормализации")
    # ДП по (S, D, I): dp[i][j] = (стоимость, s, d, i)
    rows, cols = len(ref) + 1, len(hyp) + 1
    dp = [[(0, 0, 0, 0)] * cols for _ in range(rows)]
    for i in range(1, rows):
        dp[i][0] = (i, 0, i, 0)  # все удаления
    for j in range(1, cols):
        dp[0][j] = (j, 0, 0, j)  # все вставки
    for i in range(1, rows):
        for j in range(1, cols):
            if ref[i - 1] == hyp[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
                continue
            sub = dp[i - 1][j - 1]
            dele = dp[i - 1][j]
            ins = dp[i][j - 1]
            best = min(
                (sub[0] + 1, sub[1] + 1, sub[2], sub[3]),
                (dele[0] + 1, dele[1], dele[2] + 1, dele[3]),
                (ins[0] + 1, ins[1], ins[2], ins[3] + 1),
            )
            dp[i][j] = best
    cost, s, d, ins_ = dp[-1][-1]
    return WerResult(
        wer=cost / len(ref),
        substitutions=s,
        deletions=d,
        insertions=ins_,
        ref_words=len(ref),
    )


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    ref = open(argv[1], encoding="utf-8").read()
    hyp = open(argv[2], encoding="utf-8").read()
    r = wer(ref, hyp)
    print(
        f"WER: {r.wer:.2%}  (S={r.substitutions} D={r.deletions} "
        f"I={r.insertions} N={r.ref_words})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
