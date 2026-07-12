# Architecture Decision Records (ADR)

Решения уровня «платформа / протокол / движок / лицензия» фиксируются здесь в формате
[MADR](https://adr.github.io/madr/) (упрощённый). Процесс — в [CONTRIBUTING.md](../../CONTRIBUTING.md).

Статусы: `proposed` → `accepted` → (`superseded by NNNN` | `deprecated`).
Принятый ADR не редактируется по существу — его отменяет новый ADR.

## Индекс

| № | Решение | Статус |
|---|---------|--------|
| [0001](0001-compute-platform.md) | Вычислительная платформа: RPi5 (Edge) / RPi4 (dev) / Zero 2W (thin) | accepted |
| [0002](0002-mic-array.md) | Микрофонный массив: готовый USB DSP-модуль → своя плата XVF-3800 | accepted |
| [0003](0003-vendoring-meetily.md) | Переиспользование Meetily: вендоринг скриптом, не форк | accepted |
| [0004](0004-asr-engine.md) | ASR: whisper.cpp + подключаемый интерфейс бэкендов | accepted |
| [0005](0005-tts-engine.md) | TTS: Piper (MIT, CPU) | accepted |
| [0006](0006-wake-word.md) | Wake-word: openWakeWord / Sherpa-ONNX; Porcupine — только с платной лицензией | proposed |
| [0007](0007-editions-model.md) | Редакции: одно ядро → Edge / Cloud / On-prem / гибрид | accepted |
| [0008](0008-license.md) | Лицензия проекта: Apache-2.0 (код) + CC-BY-4.0 (документация) | accepted |
| [0009](0009-ingest-protocol.md) | Протокол приёма аудио: WebSocket + JSON-заголовок + PCM-кадры (v1) | proposed |

## Шаблон

```markdown
# NNNN. Название решения

- Статус: proposed | accepted | superseded by NNNN
- Дата: YYYY-MM-DD

## Контекст и проблема
## Рассмотренные варианты
## Решение
## Последствия
```
