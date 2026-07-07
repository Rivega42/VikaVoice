# Сторонние компоненты и лицензии (THIRD-PARTY NOTICES)

Этот продукт использует и адаптирует части сторонних проектов. Ниже — атрибуция.
Файлы лицензий сохраняются при вендоринге (см. `software/scripts/vendor_meetily.sh`).
Карта заимствований — [docs/compliance/reuse-map.md](docs/compliance/reuse-map.md).

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
- Copyright (c) 2024 Zackriya Solutions. Текст лицензии — в
  `software/core/vendor/meetily/LICENSE.md` после запуска скрипта вендоринга.
- НЕ используем компоненты Meetily PRO/Enterprise (отдельная кодовая база, не MIT).

## Голосовой стек

- **whisper.cpp** — MIT (код); веса моделей Whisper — MIT.
- **Piper TTS** — MIT (код); голоса ru (irina, ruslan) — проверить лицензию конкретной модели.
- **silero-vad** — MIT.
- **openWakeWord** — Apache-2.0.
- **Sherpa-ONNX** — Apache-2.0.
- **Porcupine (Picovoice)** — ⚠️ **коммерческая лицензия**: бесплатный тариф ограничен
  (личное использование, лимиты), для продукта нужна платная лицензия Picovoice.
  Рассматривается только как платная альтернатива — см.
  [ADR-0006](docs/adr/0006-wake-word.md).

## Модели и веса (проверять отдельно от кода движков)

- **NVIDIA NeMo / Parakeet** — условия на веса моделей уточнить у NVIDIA (возможны
  ограничения по применению/юрисдикциям).
- **pyannote.audio** — код MIT; веса моделей на HuggingFace гейтятся (требуют принятия
  условий), свои условия использования.
- **Ollama** — MIT (сам инструмент).
- **Llama 3.x (Meta)** — ⚠️ веса под **Llama Community License**, не open-source в строгом
  смысле: ограничения на использование, требования атрибуции («Built with Llama»),
  порог MAU. Учитывать при выборе локальной LLM для приватного режима
  (альтернативы с более свободными лицензиями: Qwen — Apache-2.0, Phi — MIT).
- **ffmpeg** — LGPL/GPL в зависимости от сборки; учитывать при дистрибуции.

## Требование MIT

При распространении сохранять уведомление об авторских правах и текст лицензии.
Данный файл + сохранённые `LICENSE.md` вендоренных компонентов это обеспечивают.
