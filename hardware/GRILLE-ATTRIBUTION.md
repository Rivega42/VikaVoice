# Атрибуция: Апериодическая решётка

## Источник

Модели апериодической решётки для боковой поверхности корпуса VikaVoice основаны
на публикации Яндекса:

**Repository:** https://github.com/yandex/aperiodic_grille
**Original title:** "3D Models of Aperiodic Grille for Yandex Station 2"
**Author:** Yandex (Григорий Анненков — инженер, автор внедрения)
**License:** [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)
(Attribution-ShareAlike 4.0 International)

## Требования лицензии CC BY-SA 4.0

При использовании производных работ мы обязаны:

1. **Attribution (BY)** — указать авторство оригинала
   → выполнено этим файлом + ссылками в THIRD_PARTY_NOTICES.md
2. **ShareAlike (SA)** — распространять производную работу под той же лицензией
   → все наши модификации STEP/STL решётки публикуются под **CC BY-SA 4.0**
3. **No additional restrictions** — не добавляем DRM или патентные ограничения
   → выполнено
4. **Notice of changes** — указать какие изменения внесены
   → см. раздел ниже

## Что мы модифицируем

- Масштабирование под наши размеры корпуса Ø150 × H180 мм
- Адаптация центрального отверстия под наш динамик
- Возможно, изменение шага апериодического паттерна для 3D-печати FDM
- Все изменения фиксируются в git-истории `hardware/grille/`

## Файлы

- `hardware/grille/original/` — оригинальные STEP/STL/DXF (немодифицированные, из
  Яндекса, для трассируемости)
- `hardware/grille/vika/` — наши модификации
- `hardware/grille/LICENSE-CC-BY-SA-4.0.txt` — текст лицензии
