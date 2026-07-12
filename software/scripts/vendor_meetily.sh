#!/usr/bin/env bash
# Подтягивает из Meetily (MIT) только те части, которые мы переиспользуем,
# в software/core/vendor/meetily/, сохраняя файл лицензии (атрибуция MIT).
# Подход и правила — ADR-0003 (docs/adr/0003-vendoring-meetily.md).
#
# Запускать можно из ЛЮБОГО каталога:
#   bash software/scripts/vendor_meetily.sh
# Фиксация версии (рекомендуется для воспроизводимости):
#   MEETILY_REF=<тег|ветка> bash software/scripts/vendor_meetily.sh
set -euo pipefail

# Работаем относительно каталога software/, где бы нас ни запустили.
cd "$(dirname "$0")/.."

REPO="https://github.com/Zackriya-Solutions/meetily.git"
DST="core/vendor/meetily"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

if [ -n "${MEETILY_REF:-}" ]; then
  echo ">> Клонирую Meetily (закреплённый ref: $MEETILY_REF)…"
  # Никаких молчаливых fallback'ов: несуществующий ref = ошибка и выход.
  git clone --depth 1 --branch "$MEETILY_REF" "$REPO" "$TMP"
else
  echo "!! MEETILY_REF не задан — клонирую ветку апстрима по умолчанию."
  echo "!! Для воспроизводимой сборки задайте: MEETILY_REF=<тег|коммит-ветка>"
  git clone --depth 1 "$REPO" "$TMP"
fi

mkdir -p "$DST"

# Что копируем (см. docs/compliance/reuse-map.md):
COPY_PATHS=(
  "LICENSE.md"                              # обязательно: сохраняем лицензию MIT
  "backend/app"                             # FastAPI + хранение + transcript_processor (с v0.4.0 внутри app/)
  "backend/whisper-custom/server"           # HTTP-сервер Whisper
  "backend/docker-compose.yml"              # образец контейнеризации
  "backend/Dockerfile.server-cpu"
  "backend/Dockerfile.server-gpu"
  "backend/Dockerfile.server-macos"
  "backend/requirements.txt"
  "frontend/src-tauri/src/audio"            # захват системного звука (референс, Rust)
  "frontend/src-tauri/src/parakeet_engine"  # ASR Parakeet (Rust)
  "frontend/src-tauri/src/ollama"           # интеграция Ollama
)

MISSING=0
for p in "${COPY_PATHS[@]}"; do
  if [ -e "$TMP/$p" ]; then
    mkdir -p "$DST/$(dirname "$p")"
    cp -r "$TMP/$p" "$DST/$p"
    echo "   + $p"
  else
    echo "   ! пропущено (нет в апстриме): $p"
    MISSING=1
  fi
done

if [ ! -f "$DST/LICENSE.md" ]; then
  echo "!! ОШИБКА: LICENSE.md не скопирован — вендоринг без атрибуции недопустим." >&2
  exit 1
fi

echo ">> Готово. Источники в software/$DST (лицензия MIT сохранена в $DST/LICENSE.md)."
echo ">> Это MIT-код Zackriya Solutions — атрибуция в THIRD_PARTY_NOTICES.md."
[ "$MISSING" -eq 1 ] && echo ">> Внимание: часть путей отсутствует в апстриме — проверьте reuse-map."
exit 0
