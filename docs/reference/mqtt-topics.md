# MQTT-топики (multi-device)

> Статус: 🟡 design (реализация — EPIC-9; в MVP закладывается только клиент-stub) ·
> Обновлено: 2026-07-07 · Контекст: [multi-device.md](../architecture/multi-device.md)

Broker — mosquitto на hub-устройстве. Только локальная сеть; наружу MQTT не ходит.

## Топики

| Топик | Retained | Payload (JSON) | Назначение |
|-------|----------|----------------|-----------|
| `vika/state/private-mode` | ✅ | `{"on": true, "until": "<ts>", "origin": "<device>"}` | глобальный приватный режим |
| `vika/state/home-mode` | ✅ | `{"mode": "active\|passive"}` | «я ушёл/я дома» |
| `vika/state/active-conversation` | ❌ (TTL 30 c) | `{"device": "<id>", "session": "<id>"}` | кто ведёт разговор |
| `vika/timers/<timer-id>` | ✅ (per timer) | `{"fire_at": "<ts>", "scope": "local\|global", "room": "..."}` | таймеры/напоминания |
| `vika/events/wake-word` | ❌ | `{"device": "<id>", "score": 0.87, "ts": "<ts>"}` | ставки арбитража |
| `vika/arbitration/wake-word` | ❌ | см. events + окно 250 мс | арбитраж «кто отвечает» |
| `vika/broadcast/announce` | ❌ | `{"text": "...", "voice": "piper-irina"}` | «скажи всем» |
| `vika/state/user-arrived-home` | ❌ | `{"user": "<id>", "via": "mobile"}` | handoff телефон → дом |

## Правила

- Retained-топики описывают **состояние**, не события; события — не retained.
- Каждое устройство подписано на `vika/#`; фильтрация по scope — на клиенте.
- Отказ брокера: устройства работают автономно (fail-safe арбитража — отвечает каждый).
- Discovery устройств — не через MQTT, а mDNS (`_vika._tcp.local`,
  TXT: `role=hub|satellite`, `room=<...>`).

## Открытые вопросы

- Аутентификация MQTT (пароль/клиентские сертификаты) — даже в LAN, из-за
  чувствительности `private-mode`.
- Версионирование payload'ов (поле `v`, как в ingest).
