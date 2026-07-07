#!/usr/bin/env bash
# Подтягивает из Meetily (MIT) только те части, которые мы переиспользуем,
# в core/vendor/meetily/, сохраняя файл лицензии (атрибуция MIT).
#
# Запускать из корня репозитория:  bash scripts/vendor_meetily.sh
set -euo pipefail

REPO="https://github.com/Zackriya-Solutions/meetily.git"
REF="${MEETILY_REF:-main}"          # можно закрепить конкретный коммит/тег
DST="core/vendor/meetily"
TMP="$(mktemp -d)"

echo ">> Клонирую Meetily ($REF)…"
git clone --depth 1 --branch "$REF" "$REPO" "$TMP" 2>/dev/null || git clone --depth 1 "$REPO" "$TMP"

mkdir -p "$DST"

# Что копируем (см. REUSE_MAP.md):
COPY_PATHS=(
  "LICENSE.md"                              # обязательно: сохраняем лицензию MIT
  "backend/app"                             # FastAPI + хранение (main.py, db.py, ...)
  "backend/transcript_processor.py"         # LLM-резюме
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

for p in "${COPY_PATHS[@]}"; do
  if [ -e "$TMP/$p" ]; then
    mkdir -p "$DST/$(dirname "$p")"
    cp -r "$TMP/$p" "$DST/$p"
    echo "   + $p"
  else
    echo "   ! пропущено (нет в репо): $p"
  fi
done

rm -rf "$TMP"
echo ">> Готово. Источники в $DST (лицензия MIT сохранена в $DST/LICENSE.md)."
echo ">> Не забудьте: это MIT-код Zackriya Solutions — атрибуция в THIRD_PARTY_NOTICES.md."
