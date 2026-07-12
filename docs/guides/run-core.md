# Как запустить ядро (скелет)

> Статус: ✅ актуален · Обновлено: 2026-07-07 · Что именно уже работает, а что заглушка —
> честно указано ниже.

## Что есть сейчас

| Компонент | Состояние |
|-----------|-----------|
| Приём аудио по WS (`core/api/ingest_ws.py`) | ✅ рабочий скелет: заголовок → PCM-кадры → WAV; покрыт тестами (`software/tests/`) |
| Клиент-компаньон (`companion-client/`) | ✅ отправка потока и `--test`-режим; захват реального системного звука зависит от ОС/устройств — проверяйте `--list` |
| Handoff в ASR | ❌ **заглушка** — WAV пишется, транскрипции нет (EPIC-1) |
| `core/asr/base.py`, `core/voice_enrollment/` | интерфейсы; реализации — EPIC-1/2 |
| docker-compose | скелет: `ingest` собирается; `whisper` требует вендоринга; `ollama` — профиль |

## Локальный запуск (без Docker)

```bash
cd software
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# терминал 1 — ядро (порт 8200)
uvicorn core.api.ingest_ws:app --host 0.0.0.0 --port 8200

# терминал 2 — клиент шлёт 3 секунды синтетического сигнала
pip install -r companion-client/requirements.txt
python companion-client/system_audio_client.py --test
```

Результат: WAV принятого потока в `software/data/ingest_sessions/`
(каталог меняется переменной `VIKAVOICE_INGEST_DIR`).

Реальный системный звук вместо теста:

```bash
python companion-client/system_audio_client.py --list                     # устройства
python companion-client/system_audio_client.py --server ws://<IP>:8200/ingest --source system
```

⚠️ Протокол пока без аутентификации и TLS — только доверенная LAN
([подробнее](../reference/api/ingest-ws.md#ограничения-v1-зафиксированы-план--adr-0009)).

## Docker

```bash
cd software
docker compose up ingest                       # только приём аудио

# с ASR (сначала вендоринг Meetily):
bash scripts/vendor_meetily.sh                 # или MEETILY_REF=<тег> bash scripts/vendor_meetily.sh
docker compose --profile with-asr up

# с локальной LLM для резюме:
docker compose --profile with-llm up
```

## Тесты

```bash
cd software && pytest -q
```
