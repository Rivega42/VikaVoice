# Архитектура: обзор

> Статус: ✅ актуален · Обновлено: 2026-07-07 · Связанные ADR:
> [0001 платформа](../adr/0001-compute-platform.md), [0002 микрофоны](../adr/0002-mic-array.md),
> [0004 ASR](../adr/0004-asr-engine.md), [0005 TTS](../adr/0005-tts-engine.md),
> [0007 редакции](../adr/0007-editions-model.md)

## Контекст системы

```mermaid
flowchart TB
    user(("Пользователь /<br/>участники встречи"))
    pc["ПК с онлайн-встречей<br/>(клиент-компаньон)"]
    esp["ESP32-компаньон<br/>(статус-экран)"]

    subgraph device["Устройство VikaVoice (RPi5 Edge / RPi4 dev)"]
        mic["Микрофонный массив<br/>XMOS DSP: AEC, beamforming, DOA"]
        core["Локальный речевой стек:<br/>wake-word · VAD · whisper.cpp ·<br/>диаризация · enrollment · Piper TTS"]
        skills["Навыки: home · facilitator ·<br/>transcriber · private (модификатор)"]
    end

    subgraph cloud["OCPlatform (облако/контур)"]
        gw["Gateway (OpenAI-совместимый API)"]
        brain["Память Вики · личность (SOUL.md) ·<br/>инструменты · LLM (LiteLLM)"]
    end

    cabinet["Веб-кабинет:<br/>стенограммы, правка, поиск, экспорт"]
    integrations["Интеграции: Telegram · Notion ·<br/>календарь · Умный Дом Яндекс"]

    user -- голос --> mic
    mic --> core --> skills
    pc -- "WS ingest (системный звук)" --> core
    skills -- "текст (HTTPS/TLS)" --> gw --> brain
    brain -- инструменты --> integrations
    skills --> cabinet
    core -- "TTS → колонка" --> user
    esp -- "GET /status" --> core

    style device fill:#e8f4e8,stroke:#2d7d2d,color:#000
    style cloud fill:#e8ecf8,stroke:#2d4d9d,color:#000
```

В **приватном режиме** связь с облаком полностью отключается — обработка (включая LLM)
остаётся на устройстве. Подробно: [privacy-mode.md](privacy-mode.md).

## Конвейер запроса (навык «домашний ассистент»)

```mermaid
sequenceDiagram
    autonumber
    participant U as Пользователь
    participant M as Микрофонный массив (DSP)
    participant D as Устройство (RPi)
    participant G as OCPlatform Gateway

    U->>M: «Вика, что у меня сегодня?»
    M->>D: очищенный аудиопоток (AEC/beamforming)
    D->>D: wake-word детект («Вика»)
    D->>D: VAD → конец фразы → whisper.cpp (STT, ru)
    D->>G: текст запроса (HTTPS/TLS, токен устройства)
    G->>G: память + личность + инструменты → LLM
    G-->>D: текст ответа
    D->>D: Piper TTS (локально)
    D-->>U: голос из колонки + LED-индикация
```

Полный аудиотракт (VAD, диаризация, enrollment, line-in) — [audio-pipeline.md](audio-pipeline.md).

## Распределение компонентов

### Локально на устройстве

| Компонент | Технология | Зачем локально |
|-----------|-----------|----------------|
| Обработка звука | XMOS DSP (AEC, beamforming, DOA) | аппаратно, без нагрузки на CPU — [ADR-0002](../adr/0002-mic-array.md) |
| Wake-word | openWakeWord / Sherpa-ONNX | всегда слушает, без интернета — [ADR-0006](../adr/0006-wake-word.md) |
| VAD | silero-vad | детект конца фразы |
| STT | whisper.cpp (модель по платформе) | скорость + приватность — [ADR-0004](../adr/0004-asr-engine.md) |
| Диаризация | pyannote (навыки встреч) | кто говорит |
| Enrollment | голосовые отпечатки (ECAPA/pyannote) | имена участников в стенограмме |
| TTS | Piper (ru) | латентность, офлайн — [ADR-0005](../adr/0005-tts-engine.md) |
| Локальная LLM | llama.cpp / Ollama, модель 1–3B | только приватный режим — [privacy-mode.md](privacy-mode.md) |

### В облаке / контуре (OCPlatform)

| Компонент | Зачем не на устройстве |
|-----------|------------------------|
| Основная LLM | вычислительно тяжело для RPi |
| Память Вики | сохраняется между сессиями и поверхностями (устройство = тот же ассистент, что в Telegram) |
| Инструменты (календарь, задачи, интеграции) | требуют сети и учёток |
| Личность и контекст (SOUL.md, MEMORY.md) | единая личность для всех устройств |

Адрес gateway и токен — параметры конфигурации устройства
([reference/configuration.md](../reference/configuration.md)); адреса инфраструктуры в
документации не публикуются. Транспорт — только TLS.

## Навыки

Подробно — [concept/skills.md](../concept/skills.md). Сводка:

| Навык | Триггер | Активная роль | Данные наружу |
|-------|---------|---------------|---------------|
| 🏠 Home | wake-word «Вика» | разговор | → OCPlatform (TLS) |
| 🎯 Facilitator | «начнём встречу» | модерация встречи | → OCPlatform (TLS) |
| 📝 Transcriber | «просто запиши» | молча пишет + суммирует | локально; суммаризация — по редакции |
| 🔒 Private | «приватный режим» | модификатор поверх остальных | **никуда** |

## Редакции

Одно ядро обслуживает редакции Edge / Cloud / On-prem / гибрид конфигурацией —
[ADR-0007](../adr/0007-editions-model.md), технические детали — [deployment.md](deployment.md).

## Связанные документы

- [Модель данных](data-model.md) · [Деплой](deployment.md) ·
  [Наблюдаемость](observability.md) · [Модель угроз](security-threat-model.md)
- [Multi-device](multi-device.md) и [мобильный клиент](mobile.md) — 🟡 design, горизонт EPIC-9
- [Протокол ingest](../reference/api/ingest-ws.md) · [MQTT-топики](../reference/mqtt-topics.md)
