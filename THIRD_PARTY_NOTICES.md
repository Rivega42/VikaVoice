# Сторонние компоненты и лицензии (THIRD-PARTY NOTICES)

Этот продукт использует и адаптирует части сторонних проектов. Ниже — атрибуция.
Файлы лицензий сохраняются при вендоринге (см. `scripts/vendor_meetily.sh`).

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
