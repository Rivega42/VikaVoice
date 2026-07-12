# device/ — клиент устройства (появится в EPIC-5)

> Статус: 🔲 каталог-заготовка · Обновлено: 2026-07-07

Здесь будет Linux-клиент, работающий на устройстве (RPi). Это **не прошивка** в смысле
firmware (бывший каталог `firmware/` удалён — навыки, а не прошивки, различают поведение
одной Вики; см. [concept/skills.md](../../docs/concept/skills.md)).

## Что здесь появится

- Диалоговый цикл навыка home: wake-word → VAD → STT → OCPlatform → Piper TTS → колонка
  (EPIC-5, [roadmap](../../docs/roadmap.md)).
- Управление LED-кольцом и кнопками (EPIC-4).
- Роутер режимов: OCPlatformClient ↔ LocalLlamaClient, network-kill приватного режима
  (EPIC-6, [privacy-mode](../../docs/architecture/privacy-mode.md)).
- MQTT client-stub и mDNS-анонс — задел под multi-device (EPIC-9).

## Контракты

- Конфиг: [`docs/reference/configuration.md`](../../docs/reference/configuration.md)
- Протокол отправки аудио в ядро: [`docs/reference/api/ingest-ws.md`](../../docs/reference/api/ingest-ws.md)
- Слой микрофонного массива: [`core/mic_array/`](../core/mic_array/README.md)
