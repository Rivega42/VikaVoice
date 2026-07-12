# Карта переиспользования (REUSE MAP)

> Статус: ✅ актуален · Обновлено: 2026-07-07 · Связанные ADR:
> [0003 вендоринг Meetily](../adr/0003-vendoring-meetily.md) ·
> Атрибуция: [THIRD_PARTY_NOTICES.md](../../THIRD_PARTY_NOTICES.md)

Что берём из внешних проектов и что пишем сами. Привязано к реальным путям в
репозитории Meetily (github.com/Zackriya-Solutions/meetily, лицензия MIT),
проверенным по коду.

Легенда статуса:

- **BORROW** — берём код/подход из Meetily (MIT), адаптируем.
- **REFERENCE** — используем как образец архитектуры, пишем своё.
- **BUILD** — строим сами, в Meetily этого нет.

---

## 1. Звуковой тракт устройства (микрофонный массив)

| Блок | Статус | Источник / примечание |
|------|--------|-----------------------|
| Круговой MEMS-массив, beamforming, DOA, эхоподавление | **BUILD** | В Meetily отсутствует. Реализуется на прошивке массива (XVF-3800) либо на устройстве. Это наше аппаратное преимущество. |
| Захват многоканального аудио, VAD, ресемплинг | **REFERENCE** | Meetily: `frontend/src-tauri/src/audio/` — `vad.rs`, `stream.rs`, `decoder.rs` (symphonia), ресемплинг `rubato`. Подход берём, код на Rust — под десктоп; на устройстве проще на Python/C. |

## 2. Захват системного звука (ПК-звук онлайн-встреч)

| Путь | Статус | Источник / примечание |
|------|--------|-----------------------|
| Программный (клиент-компаньон) | **BORROW/BUILD** | Meetily делает через `cpal`: Windows — WASAPI loopback (`audio/core-old.rs`), Linux — PulseAudio monitor, macOS — ScreenCaptureKit; микширование mic+system через ffmpeg (`audio/ffmpeg_mixer.rs`). Мы даём свой лёгкий клиент (`software/companion-client/`, Python) + опция форкнуть их Rust-захват. |
| Аппаратный (проводом) | **BUILD** | В Meetily нет (десктоп берёт звук программно). У нас — линейный вход в устройство (USB-аудио line-in / 3.5 мм / HDMI-аудио экстрактор), см. [guides/hardware-line-in.md](../guides/hardware-line-in.md). |

## 3. Распознавание речи (ASR)

| Блок | Статус | Источник / примечание |
|------|--------|-----------------------|
| Движок Whisper (локально) | **BORROW** | Meetily: `backend/whisper-custom/server`, `backend/whisper.cpp`, сборки `Dockerfile.server-{cpu,gpu,macos}`. HTTP-сервер транскрипции, порт 8178. Русский — через `WHISPER_LANGUAGE=ru`. |
| Движок Parakeet (Rust) | **BORROW** | Meetily: `frontend/src-tauri/src/parakeet_engine/`. Быстрее Whisper, хорош на Jetson. Веса — условия NVIDIA проверить. |
| Подключаемый ASR-бэкенд (интерфейс) | **BUILD** | Meetily жёстко связывает движки. Мы делаем единый интерфейс (`software/core/asr/base.py`): локальный Whisper / Parakeet / внешнее API — выбор конфигом под редакцию ([ADR-0004](../adr/0004-asr-engine.md)). |

## 4. Диаризация и именование участников

| Блок | Статус | Источник / примечание |
|------|--------|-----------------------|
| Базовая диаризация (кто-то1/кто-то2) | **REFERENCE** | Meetily: флаг `WHISPER_DIARIZE` (tinydiarize в whisper.cpp) — грубое разделение на 2 говорящих. Продвинутая диаризация у них ушла в PRO (не MIT). |
| Запоминание голоса + подстановка имени (voice enrollment) | **BUILD** | В открытой версии Meetily нет (в README — «Coming Soon»/PRO). Наша ключевая фича «представился → узнаётся по имени». Реализуем на голосовых отпечатках: pyannote / ECAPA-TDNN / SpeechBrain. См. `software/core/voice_enrollment/`. |

## 5. Смысловой анализ (резюме, задачи)

| Блок | Статус | Источник / примечание |
|------|--------|-----------------------|
| Резюме через локальную LLM (Ollama) | **BORROW** | Meetily: `backend/transcript_processor.py`, `frontend/src-tauri/src/ollama/`, `llama-helper/`. Поддержка Ollama (локально) + OpenAI-совместимые API. Ложится в наш блок «Аналитика» и работает офлайн (Edge/on-prem). |
| Извлечение поручений, аналитика участия | **REFERENCE/BUILD** | Частично покрыто summary-промптами; извлечение задач и talk-time — дорабатываем/пишем. |

## 6. Хранение, API, кабинет

| Блок | Статус | Источник / примечание |
|------|--------|-----------------------|
| API и хранение стенограмм | **BORROW** | Meetily: `backend/app/main.py` (FastAPI), `backend/app/db.py` (SQLite), `schema_validator.py`. Хорошая стартовая точка для нашего сервиса. |
| Контейнеризация ядра | **BORROW** | Meetily: `backend/docker-compose.yml` (whisper-server + app). Адаптируем под три редакции (Edge/Cloud/On-prem). |
| Веб-кабинет (поиск, правка, экспорт, роли) | **BUILD** | Meetily-фронт — десктоп на Tauri/Next.js под онлайн-встречи. Наш кабинет — отдельный веб-UI. Часть компонентов Next.js можно подсмотреть. |

## 7. Голосовой ассистент (вне Meetily)

| Блок | Статус | Источник / примечание |
|------|--------|-----------------------|
| Wake-word | **BORROW (open-source)** | openWakeWord / Sherpa-ONNX (Apache-2.0). ⚠️ Porcupine — коммерческая лицензия, только как платная опция ([ADR-0006](../adr/0006-wake-word.md)). |
| TTS | **BORROW (open-source)** | Piper (MIT), [ADR-0005](../adr/0005-tts-engine.md). |
| Локальная LLM приватного режима | **BORROW (веса!)** | llama.cpp/Ollama — MIT; ⚠️ веса Llama — Llama Community License (ограничения); свободные альтернативы: Qwen (Apache-2.0), Phi (MIT). |

## 8. Compliance и локализация

| Блок | Статус | Источник / примечание |
|------|--------|-----------------------|
| 152-ФЗ (биометрия/ПДн), согласия, шифрование, роли | **BUILD** | В Meetily нет. Наш слой — [152fz.md](152fz.md). |
| Локализация RU, документация по 44-ФЗ | **BUILD** | Наш слой — [44fz.md](44fz.md). |

---

## Границы лицензий (важно)

- **Meetily Community** — MIT: форк, правка, коммерция, self-host разрешены. Сохраняем
  текст лицензии и атрибуцию ([THIRD_PARTY_NOTICES.md](../../THIRD_PARTY_NOTICES.md)).
- **Meetily PRO/Enterprise** — отдельная кодовая база, НЕ MIT. Не используем и не
  зависим от её функций.
- **Лицензии моделей проверяем отдельно от кода движка:**
  - whisper.cpp — MIT (код); веса моделей Whisper — MIT.
  - Parakeet / NVIDIA NeMo — уточнить условия использования весов (могут быть
    ограничения на коммерцию/юрисдикции).
  - pyannote — код MIT, но веса на HuggingFace гейтятся и имеют свои условия.
  - Ollama — MIT; лицензии конкретных LLM (Llama Community License и др.) — отдельно.
  - Porcupine — коммерческая (Picovoice), бесплатный тариф непригоден для продукта.

## Итог одной строкой

Берём у Meetily **программное ядро** (Whisper/Parakeet + Ollama-резюме + FastAPI/хранение +
Docker + подход к захвату системного звука). Сами строим **звуковой тракт массива**,
**запоминание голоса и именование**, **три редакции/контейнеризацию под них**, **аппаратный
захват системного звука**, **веб-кабинет**, **локализацию и compliance**.
