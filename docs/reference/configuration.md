# Конфигурация

> Статус: 🔴 черновик (реализовано только `VIKAVOICE_INGEST_DIR`; остальное — целевой
> контракт) · Обновлено: 2026-07-07

## Переменные окружения ядра (реализовано/используется в скелете)

| Переменная | По умолчанию | Назначение |
|-----------|--------------|-----------|
| `VIKAVOICE_INGEST_DIR` | `data/ingest_sessions` | каталог записи сессий ingest (в docker-образе — `/data/ingest_sessions`) |
| `VIKAVOICE_INGEST_TOKEN` | — (открытый режим) | если задан — ingest требует поле `token` в заголовке сессии ([протокол](api/ingest-ws.md)) |
| `EDITION` | `edge` | `edge` \| `cloud` \| `onprem` — см. [deployment](../architecture/deployment.md) |
| `ASR_BACKEND` | `whisper` | `whisper` \| `remote` — см. `core/asr/base.py` |
| `WHISPER_URL` | `http://whisper:8178/inference` | адрес вендоренного whisper-сервера |
| `WHISPER_MODEL` | `models/ggml-base.bin` | модель whisper.cpp |
| `WHISPER_LANGUAGE` | `ru` | язык распознавания |
| `VIKAVOICE_DB` | `data/vikavoice.db` | SQLite сессий/стенограмм/профилей голосов |
| `VIKAVOICE_DIARIZER` | `single` | диаризатор (`single` — заглушка до выбора движка, E2.1) |
| `VIKAVOICE_EMBEDDER` | — | эмбеддер голоса для «Знакомства» (E2.2; не задан — 501) |
| `SUMMARY_BACKEND` | `ollama` | `ollama` \| `openai` (OpenAI-совместимый OCPlatform/облако) |
| `OLLAMA_HOST` / `SUMMARY_MODEL` | `http://localhost:11434` / `qwen2.5:3b` | локальная LLM протокола |
| `LLM_BASE_URL` / `LLM_API_KEY` | — | для `SUMMARY_BACKEND=openai`; секреты только в окружении |

## Конфиг устройства `/etc/vikavoice/config.yaml` (целевой контракт, EPIC-5/7)

```yaml
device:
  name: vika-kitchen        # hostname/mDNS: vika-kitchen.local
  room: kitchen
  tier: thick               # thick | thin

ocplatform:
  url: https://...          # ТОЛЬКО https; адрес задаётся при настройке, не в репозитории
  token: "..."              # права файла 0600; вводится через AP-режим настройки

audio:
  mic_array: auto           # auto | xvf3000 | xvf3800
  line_in: null             # ALSA-устройство линейного входа, если подключён
  tts_voice: ru_irina       # piper-голос

skills:
  default: home             # home | facilitator | transcriber
  facilitator_wake: "начнём встречу"

privacy:
  default_timer_min: 120    # таймер приватного режима по умолчанию
  strict_profile: false     # true = L3: без MQTT/LAN-исключений (см. privacy-mode)

retention:
  default_policy: transcript_only   # keep_all | transcript_only | ephemeral
```

Правила: секреты не в git и не в образе; файл читается только root/сервисом;
изменение — через `vika.local/settings` ([ap-setup](../integrations/ap-setup.md)).

## Открытые вопросы

- Валидация конфига при старте (pydantic-схема) и поведение при битом конфиге
  (жёлтый пульс LED «нужна настройка»).
- Миграции конфига между версиями прошивки.
