# Как запустить ядро (скелет)

> Статус: ✅ актуален · Обновлено: 2026-07-07 · Что именно уже работает, а что заглушка —
> честно указано ниже.

## Что есть сейчас

| Компонент | Состояние |
|-----------|-----------|
| Приём аудио по WS (`core/api/ingest_ws.py`) | ✅ рабочий скелет: заголовок → PCM-кадры → WAV; покрыт тестами (`software/tests/`) |
| Клиент-компаньон (`companion-client/`) | ✅ отправка потока и `--test`-режим; захват реального системного звука зависит от ОС/устройств — проверяйте `--list` |
| Handoff в ASR | ✅ сессия регистрируется в SQLite (`queued`); транскрибация — `POST /sessions/{id}/transcribe` |
| `core/asr/base.py` | ✅ `LocalWhisper` реализован (вендоренный whisper.cpp-сервер, `verbose_json`) |
| `core/storage/db.py`, `core/metrics/wer.py` | ✅ хранение сессий/стенограмм; WER-метрика |
| `core/voice_enrollment/` | интерфейс; эмбеддер — EPIC-2 |
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

Аутентификация: задайте `VIKAVOICE_INGEST_TOKEN` на ядре и то же значение полем
`token` в заголовке клиента. TLS терминируйте реверс-прокси
([подробнее](../reference/api/ingest-ws.md)).

## Стенограмма записанной сессии

```bash
curl http://localhost:8200/sessions                          # список, статус queued/done/error
curl -X POST http://localhost:8200/sessions/<id>/transcribe  # прогнать ASR (нужен whisper-сервер)
curl http://localhost:8200/sessions/<id>/transcript          # сегменты с таймингами
```

Протокол встречи (нужна LLM: Ollama локально или OpenAI-совместимый endpoint):

```bash
curl -X POST http://localhost:8200/sessions/<id>/summarize   # построить протокол
curl http://localhost:8200/sessions/<id>/protocol            # JSON + talk-time + Markdown
```

Сценарий «Знакомство» (голосовые профили; нужен эмбеддер — E2.2):
`POST /enroll/start` (с `"consent": true`!) -> `POST /enroll/{id}/audio` -> `finish`;
`DELETE /profiles/{name}` — безусловное удаление; `POST /profiles/end-meeting` —
зачистка отпечатков «на встречу».

Оценка качества: `python -m core.metrics.wer reference.txt hypothesis.txt`,
DER — `core/metrics/der.py`.

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
