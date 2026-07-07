# Документация VikaVoice — индекс

> Единая точка входа. Структура — по [Diátaxis](https://diataxis.fr/): концепция и
> архитектура (explanation), справочники (reference), гайды (how-to), решения (ADR).
> Статусы: ✅ актуален · 🟡 design (спроектировано, не реализовано) · 🔴 черновик · 🔲 заготовка.

## Начните отсюда

1. [Концепция](concept/vision.md) — что строим, для кого, этапы зрелости
2. [Архитектура: обзор](architecture/overview.md) — как устроена система
3. [Roadmap](roadmap.md) — эпики EPIC-0..9 с задачами
4. [Как запустить ядро](guides/run-core.md) — потрогать руками за 5 минут

## Концепция (concept/)

| Документ | О чём | Статус |
|----------|-------|--------|
| [vision.md](concept/vision.md) | Цельная концепция, две ипостаси продукта, этапы | ✅ |
| [skills.md](concept/skills.md) | Навыки: home / facilitator / transcriber / private | ✅ |
| [scenarios.md](concept/scenarios.md) | Сценарии встреч: знакомство / встреча / после | ✅ |
| [editions.md](concept/editions.md) | Линейка: 2 железа × редакции Edge/Cloud/On-prem | ✅ |
| [market.md](concept/market.md) | Конкуренты, сегменты, ценообразование | 🔴 |

## Архитектура (architecture/)

| Документ | О чём | Статус |
|----------|-------|--------|
| [overview.md](architecture/overview.md) | Контекст системы, конвейер, распределение компонентов | ✅ |
| [audio-pipeline.md](architecture/audio-pipeline.md) | Тракт: массив → VAD → ASR → диаризация → enrollment | 🟡 |
| [privacy-mode.md](architecture/privacy-mode.md) | Приватный режим: уровни гарантий, проверяемость | 🟡 |
| [data-model.md](architecture/data-model.md) | Сущности, биометрия, retention, хранилище | 🟡 |
| [deployment.md](architecture/deployment.md) | Редакции технически, поставка, секреты, OTA | 🟡 |
| [observability.md](architecture/observability.md) | Логи, метрики, health; телеметрия off в Edge | 🟡 |
| [security-threat-model.md](architecture/security-threat-model.md) | Активы, угрозы T1–T10, честные статусы | 🟡 |
| [multi-device.md](architecture/multi-device.md) | Несколько Вик: arbitration, handoff, MQTT | 🟡 EPIC-9 |
| [mobile.md](architecture/mobile.md) | Вика в наушниках: PWA / native / WebRTC | 🟡 EPIC-9 |

## Решения (adr/)

[Индекс ADR](adr/README.md): 0001 платформа · 0002 микрофоны · 0003 вендоринг Meetily ·
0004 ASR · 0005 TTS · 0006 wake-word · 0007 редакции · 0008 лицензия · 0009 протокол ingest.

## Справочники (reference/)

| Документ | О чём | Статус |
|----------|-------|--------|
| [api/ingest-ws.md](reference/api/ingest-ws.md) | Протокол приёма аудио v1 (WS) | ✅ |
| [mqtt-topics.md](reference/mqtt-topics.md) | Топики координации multi-device | 🟡 |
| [configuration.md](reference/configuration.md) | env-переменные и config.yaml устройства | 🔴 |

## Гайды (guides/)

| Документ | О чём | Статус |
|----------|-------|--------|
| [run-core.md](guides/run-core.md) | Запуск ядра и клиента-компаньона | ✅ |
| [hardware-line-in.md](guides/hardware-line-in.md) | Звук ПК проводом в устройство | ✅ |
| build-mvp.md | Сборка устройства от коробки до стенограммы | 🔲 EPIC-4 |

## Железо (hardware/)

| Документ | О чём | Статус |
|----------|-------|--------|
| [bom-edge.csv](hardware/bom-edge.csv) | BOM толстого устройства (RPi5), база — $356 | ✅ |
| [bom-options.csv](hardware/bom-options.csv) | Опции Edge (+$129) | ✅ |
| [bom-thin.csv](hardware/bom-thin.csv) | BOM тонкого устройства (Zero 2W) — $147 | ✅ |
| [bom-notes.md](hardware/bom-notes.md) | Сводка, допущения, NRE | ✅ |
| [bom-mvp.md](hardware/bom-mvp.md) | Домашний MVP на RPi4 (dev) | 🟡 историческая |

CAD/схемы/серийная плата — каталог [`hardware/`](../hardware/README.md) в корне репозитория.

## Интеграции (integrations/)

[Индекс интеграций](integrations/README.md): Умный Дом Яндекс · ESP32-компаньон ·
AP-режим настройки · календарь/мессенджеры.

## Compliance (compliance/)

| Документ | О чём | Статус |
|----------|-------|--------|
| [152fz.md](compliance/152fz.md) | ПДн и биометрия: сделано/требуется/открытые вопросы | 🔴 |
| [44fz.md](compliance/44fz.md) | Закупки; черновик ТЗ — [procurement/TZ_44FZ.md](../procurement/TZ_44FZ.md) | 🔴 |
| [reuse-map.md](compliance/reuse-map.md) | Что берём из Meetily (MIT) / что строим сами | ✅ |

## Правила ведения документации

- Каждый документ — с шапкой: статус, дата, связанные ADR.
- Диаграммы — mermaid (рендерится на GitHub).
- Одна цифра — один источник истины; остальные ссылаются.
- Решения уровня платформа/протокол/движок/лицензия — только через ADR
  ([CONTRIBUTING](../CONTRIBUTING.md)).
