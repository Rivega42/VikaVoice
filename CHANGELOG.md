# Changelog

Формат — [Keep a Changelog](https://keepachangelog.com/ru/1.1.0/); версии пока не тегируются
(концепт-стадия), записи группируются по датам.

## [Unreleased] — 2026-07-07

### Добавлено

- LICENSE (Apache-2.0 для кода; документация — CC-BY-4.0, см. README), CONTRIBUTING, CHANGELOG.
- `.github/`: CI (markdownlint, проверка ссылок, ruff, pytest), шаблоны issue и PR.
- ADR 0001–0009 (формат MADR): платформа, микрофонный массив, вендоринг Meetily, ASR, TTS,
  wake-word, редакции, лицензия, протокол ingest.
- Новые архитектурные документы: модель данных, деплой редакций, наблюдаемость,
  модель угроз, приватный режим, аудиотракт.
- `docs/reference/`: спецификация протокола ingest (WS), MQTT-топики, конфигурация.
- Тесты `software/tests/` (enrollment, ingest WS); `pyproject.toml`, `docker/Dockerfile.ingest`.
- `docs/hardware/bom-edge.csv`, `bom-thin.csv`, `bom-options.csv` — BOM как диффабельные CSV.
- `procurement/TZ_44FZ.md` — черновик ТЗ в Markdown (исходник вместо бинарника).

### Изменено

- Документация реструктурирована по Diátaxis: `docs/{concept,architecture,adr,reference,guides,hardware,integrations,compliance}/`, единый индекс `docs/README.md`.
- Roadmap переписан в эпики EPIC-0..9; транскрайбер идёт раньше голосового ассистента.
- ASCII-диаграммы заменены на mermaid.
- `ingest_ws.py`: JSON-заголовок обязателен первым сообщением, uuid-имена сессий,
  конфигурируемый каталог записи (`VIKAVOICE_INGEST_DIR`).
- `vendor_meetily.sh`: работает из любого каталога, явное поведение `MEETILY_REF`.
- Из документов убраны адреса инфраструктуры и личные детали; терминология унифицирована
  (везде «OCPlatform»); заявления «работает/протестировано» заменены честными статусами.

### Удалено

- `_МАНИФЕСТ.md` (его роль — этот файл и индекс `docs/README.md`).
- `engineering/BOM.xlsx` (заменён CSV в `docs/hardware/`), пустые каталоги `firmware/*`.
- Дублирующие документы: `docs/CONCEPT.md`, `docs/MEETING-COMPLEX-INDEX.md`,
  `docs/INTEGRATIONS.md`, `docs/COMPLIANCE-44FZ-152FZ.md` — содержимое перенесено.

## 2026-07-07 и ранее — история до реструктуризации

Хронология по git-истории:

- `init: концепция, архитектура, BOM, roadmap` — README, CONCEPT, ARCHITECTURE, SKILLS,
  ROADMAP, HARDWARE-BOM; каталоги firmware/, hardware/.
- `refactor: навыки Вики вместо прошивок + приватный режим` — модель «одна Вика, несколько
  навыков», приватный режим как модификатор.
- `docs: интеграции — УДЯ, ESP-компаньон, AP-режим настройки`.
- `docs: MULTI-DEVICE — несколько Вик как единая система` — arbitration, handoff, MQTT.
- `feat: транскрайбер — полный инженерный пакет (из архива)` — второй слой материалов
  («переговорный комплекс»): USER-SCENARIOS, DEPLOYMENT-EDITIONS, REUSE-MAP,
  COMPLIANCE-44FZ-152FZ, MEETING-COMPLEX-INDEX; `software/` (приём аудио по WebSocket,
  клиент захвата системного звука, интерфейсы ASR и enrollment, вендоринг Meetily);
  `procurement/TZ_44FZ.docx` (черновик ТЗ по 44-ФЗ: 10 разделов + таблица 62 характеристик);
  `engineering/BOM.xlsx` (Edge / тонкое устройство / сводка); THIRD_PARTY_NOTICES.
- `docs: MOBILE — Вика в наушниках через телефон` — PWA / native / WebRTC.

Известное следствие того периода: два слоя документации противоречили друг другу
(RPi4 vs RPi5, два BOM, разные модели продукта). Разрешено в ADR-0001/0002 и
реструктуризации выше.
