# Комплекс записи и транскрибации — указатель

Материалы по навыкам **«Фасилитатор встреч»** и **«Транскрайбер»**: настольное
устройство с круговым микрофонным массивом, распознавание по ролям, запоминание
голосов участников, протоколы и поручения.

## Документы
- [USER-SCENARIOS.md](USER-SCENARIOS.md) — сценарии: знакомство (запоминание голосов),
  живая встреча, после встречи.
- [DEPLOYMENT-EDITIONS.md](DEPLOYMENT-EDITIONS.md) — редакции ПО (Edge / Cloud / On-premise /
  гибрид) и два аппаратных исполнения.
- [REUSE-MAP.md](REUSE-MAP.md) — что берём из Meetily (MIT) и что пишем сами.
- [COMPLIANCE-44FZ-152FZ.md](COMPLIANCE-44FZ-152FZ.md) — закупки и биометрия.

## Деливераблы
- [../procurement/TZ_44FZ.docx](../procurement/TZ_44FZ.docx) — ТЗ по 44-ФЗ (10 разделов +
  таблица из 62 характеристик, без иностранных терминов).
- [../engineering/BOM.xlsx](../engineering/BOM.xlsx) — ведомость материалов
  (Edge / тонкое устройство / сводка с пересчётом в рубли).

## Программный каркас (`../software/`)
- `core/api/ingest_ws.py` — приём аудио по WebSocket (проверено сквозным тестом).
- `companion-client/` — программный захват системного звука ПК (WASAPI/Pulse/ScreenCaptureKit).
- `docs/hardware_line_in.md` — аппаратный захват системного звука (проводом).
- `core/asr/base.py`, `core/voice_enrollment/enroll.py` — интерфейсы ASR и запоминания голоса.
- `scripts/vendor_meetily.sh` — подтягивает нужные части Meetily (MIT) с атрибуцией.
