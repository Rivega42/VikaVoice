# Клиент-компаньон: программный захват системного звука

Захватывает системный звук ПК (звук онлайн-встречи) и/или микрофон и стримит его
в ядро по WebSocket. Аналог того, как это делает десктоп Meetily, но отдельным
лёгким клиентом, который шлёт поток на наше устройство/сервер.

## Установка

```bash
pip install -r requirements.txt
```

## Запуск

```bash
# показать аудиоустройства
python system_audio_client.py --list

# системный звук -> ядро
python system_audio_client.py --server ws://<IP-ядра>:8200/ingest --source system

# система + микрофон (микс)
python system_audio_client.py --source both

# проверка сквозного пути без звуковых устройств (синтетический сигнал)
python system_audio_client.py --test
```

## Как захватывается системный звук по ОС

| ОС | Механизм | Примечание |
|----|----------|------------|
| Windows | WASAPI loopback | Работает «из коробки» через loopback динамика по умолчанию. |
| Linux | PulseAudio/PipeWire monitor | Захват monitor-источника динамика. |
| macOS | Виртуальное устройство (BlackHole) или ScreenCaptureKit | Прямого loopback нет; ставится виртуальный аудиодрайвер, звук маршрутизируется в него. |

Библиотека `soundcard` даёт кроссплатформенный loopback для Windows/Linux. На macOS
для чистого решения — путь ScreenCaptureKit (как в Meetily, `frontend/src-tauri/src/audio`),
который можно форкнуть, если нужен нативный клиент без виртуального устройства.

## Формат потока (протокол v1)

- Первое сообщение — **обязательный** JSON-заголовок:
  `{"v":1,"rate":16000,"format":"pcm_s16le","channels":1,"source":"system"}`
- Далее — бинарные кадры PCM 16 кГц / 16 бит / моно по 100 мс.
- Приёмная сторона — `core/api/ingest_ws.py` (эндпоинт `/ingest`).
- Полная спецификация: [`docs/reference/api/ingest-ws.md`](../../docs/reference/api/ingest-ws.md)
  (ADR-0009). ⚠️ Пока без аутентификации и TLS — только доверенная LAN.

## Статус

Сквозной путь «клиент → WebSocket → запись WAV в ядре» покрыт автотестами
(`software/tests/test_ingest_ws.py`) и проверяется режимом `--test` (3 с синуса).
Захват реального системного звука зависит от ОС и аудиоустройств — проверяйте `--list`.
