# hardware/ — конструктив и электроника

> Статус: 🟡 в работе (промдизайн корпуса) · Обновлено: 2026-07-07 · Связанные ADR:
> [0001 платформа](../docs/adr/0001-compute-platform.md),
> [0002 микрофонный массив](../docs/adr/0002-mic-array.md)

Каталог аппаратных артефактов. Прототип собирается из готовых модулей
по единому BOM ([docs/hardware/](../docs/hardware/README.md)).

## Что уже есть

- [INDUSTRIAL-DESIGN.md](INDUSTRIAL-DESIGN.md) — форм-фактор (цилиндр Ø150×H180),
  компоновка, апериодическая решётка, материалы; открытый вопрос по ткани.
- [CASE-COVER.md](CASE-COVER.md) — кожух: DIY-опыт сообщества (yaboard/4pda),
  bayonet-съём, микрофонная прозрачность ткани.
- `grille/original/` — CAD решётки Яндекса (STEP/STL/DXF); `grille/vika/` — наша
  адаптация под Ø150 (в работе). Лицензия CC BY-SA 4.0 —
  [GRILLE-ATTRIBUTION.md](GRILLE-ATTRIBUTION.md).
- BOM пилотной партии 3 шт (корпуса — SLA-смола) —
  [docs/hardware/bom-pilot.md](../docs/hardware/bom-pilot.md).

## Что здесь появится

- `cad/` — финальные 3D-модели корпуса под сборку — EPIC-7 (E7.4).
- `schematics/` — схемы подключения кнопок, LED-кольца, аппаратного mute,
  line-in — EPIC-4.
- `mic-array/` — собственная плата 6–8 MEMS на XVF-3800 для серии (плата + прошивка,
  NRE — см. [единый BOM](../docs/hardware/README.md)) — не раньше пилотов (EPIC-8).

## Правила

- Исходники (KiCad, STEP/STL, SCAD) — сюда; ведомости материалов — в `docs/hardware/`
  как CSV (диффабельны).
- Каждое существенное аппаратное решение — через ADR (шаблон issue «Hardware»).
