# software/ — программное ядро (скелет)

> Статус: 🟡 скелет · Обновлено: 2026-07-07 · Связанные документы:
> [гайд запуска](../docs/guides/run-core.md), [reuse-map](../docs/compliance/reuse-map.md),
> [ADR-0003 вендоринг](../docs/adr/0003-vendoring-meetily.md),
> [ADR-0009 протокол ingest](../docs/adr/0009-ingest-protocol.md)

Ядро продукта записи и транскрибации переговоров: берём программную базу из
**Meetily** (MIT), строим вокруг неё наш звуковой тракт, запоминание голоса, три
редакции и оба пути захвата системного звука.

Карта переиспользования — [`docs/compliance/reuse-map.md`](../docs/compliance/reuse-map.md).
Атрибуция сторонних лицензий — [`THIRD_PARTY_NOTICES.md`](../THIRD_PARTY_NOTICES.md).

## Структура

```text
software/
├── docker-compose.yml            # ядро -> Edge/Cloud/On-prem через env (ADR-0007)
├── docker/Dockerfile.ingest      # образ сервиса ingest
├── pyproject.toml                # пакет core + dev-зависимости (pytest, ruff)
├── requirements.txt              # рантайм-зависимости ядра
├── scripts/
│   └── vendor_meetily.sh         # подтягивает части Meetily в core/vendor/ (MIT, с лицензией)
├── core/
│   ├── api/ingest_ws.py          # приём аудио по WebSocket (скелет, покрыт тестами)
│   ├── asr/base.py               # подключаемый ASR-бэкенд (интерфейс; реализации — EPIC-1)
│   ├── voice_enrollment/enroll.py# запоминание голоса + именование (интерфейс; эмбеддер — EPIC-2)
│   ├── mic_array/README.md       # слой аппаратного массива (beamforming/DOA) — EPIC-4
│   └── vendor/                   # сюда vendor_meetily.sh кладёт код Meetily (в .gitignore)
├── companion-client/             # программный захват системного звука ПК
│   └── system_audio_client.py    # стриминг в ядро; --test работает без аудиоустройств
├── device/                       # клиент устройства (wake-word, TTS, LED) — появится в EPIC-5
└── tests/                        # pytest: enrollment + контракт ingest-протокола
```

## Честный статус компонентов

| Компонент | Состояние |
|-----------|-----------|
| `core/api/ingest_ws.py` | ✅ скелет работает: заголовок → PCM → WAV; есть тесты |
| `companion-client` | ✅ `--test`-режим (синус) проходит сквозной путь; реальный захват зависит от ОС |
| handoff в ASR | ❌ **заглушка** — транскрипции пока нет (EPIC-1) |
| `core/asr`, `core/voice_enrollment` | интерфейсы без реализаций (EPIC-1/2) |
| `core/mic_array` | только описание слоя (EPIC-4) |

## Быстрый старт

Полный гайд — [`docs/guides/run-core.md`](../docs/guides/run-core.md). Кратко:

```bash
cd software
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

uvicorn core.api.ingest_ws:app --port 8200          # терминал 1: ядро
python companion-client/system_audio_client.py --test  # терминал 2: тестовый поток
# результат: WAV в software/data/ingest_sessions/

pytest -q   # тесты
```

## Вендоринг Meetily

```bash
bash scripts/vendor_meetily.sh                       # ветка апстрима по умолчанию
MEETILY_REF=<тег|коммит> bash scripts/vendor_meetily.sh   # воспроизводимо (рекомендуется)
```

Скрипт можно запускать из любого каталога; код ложится в `software/core/vendor/meetily/`
(в `.gitignore`), лицензия MIT сохраняется обязательно.

## Захват системного звука — два пути

- **Программный** — `companion-client/` (клиент на ПК шлёт поток в ядро). Windows: WASAPI
  loopback, Linux: Pulse/PipeWire monitor, macOS: BlackHole/ScreenCaptureKit.
- **Аппаратный** — проводом в линейный вход устройства:
  [`docs/guides/hardware-line-in.md`](../docs/guides/hardware-line-in.md).

## Что строить дальше

См. [roadmap](../docs/roadmap.md): привязка whisper/parakeet к `core/asr/base.py` (EPIC-1),
эмбеддер голоса для enrollment (EPIC-2), смысловой слой (EPIC-3), звуковой тракт массива
(EPIC-4), клиент устройства в `device/` (EPIC-5).
