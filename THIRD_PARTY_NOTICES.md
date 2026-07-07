# Сторонние компоненты и лицензии (THIRD-PARTY NOTICES)

Этот продукт использует и адаптирует части сторонних проектов. Ниже — атрибуция.
Файлы лицензий сохраняются при вендоринге (см. `scripts/vendor_meetily.sh`).

## Yandex Aperiodic Grille — CC BY-SA 4.0
- Репозиторий: https://github.com/yandex/aperiodic_grille
- Автор: Yandex (Григорий Анненков, инженер внедрения)
- Статья: https://habr.com/ru/companies/yandex/articles/673192/
- Используем: 3D-модель апериодической решётки для боковой поверхности корпуса VikaVoice.
- Лицензия: [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)
- Наши модификации (масштаб и адаптация под наши размеры) тоже публикуются под CC BY-SA 4.0.
- Атрибуция: [hardware/GRILLE-ATTRIBUTION.md](hardware/GRILLE-ATTRIBUTION.md)

## Meetily (Zackriya Solutions) — MIT
- Репозиторий: https://github.com/Zackriya-Solutions/meetily
- Используем (Community, MIT): движок Whisper-сервера, интеграцию Parakeet и Ollama,
  FastAPI-бэкенд и хранение, docker-compose, подход к захвату системного звука.
- Copyright (c) 2024 Zackriya Solutions. Текст лицензии — в `core/vendor/meetily/LICENSE.md`
  после запуска скрипта вендоринга.
- НЕ используем компоненты Meetily PRO/Enterprise (отдельная кодовая база, не MIT).

## Апстрим-зависимости (проверять отдельно)
- whisper.cpp — MIT (код и веса моделей Whisper).
- NVIDIA NeMo / Parakeet — условия на веса моделей уточнить у NVIDIA (возможны
  ограничения по применению/юрисдикциям).
- pyannote.audio — код MIT; веса моделей на HuggingFace гейтятся, свои условия.
- Ollama — MIT; лицензии конкретных LLM (напр. Llama) — отдельно.
- ffmpeg — LGPL/GPL в зависимости от сборки; учитывать при дистрибуции.

Требование MIT: при распространении сохранять уведомление об авторских правах и
текст лицензии. Данный файл + сохранённые `LICENSE.md` это обеспечивают.
