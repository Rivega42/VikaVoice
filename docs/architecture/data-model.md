# Модель данных

> Статус: 🟡 design (скелет; реализация — EPIC-1..3, EPIC-7) · Обновлено: 2026-07-07 ·
> Связанные документы: [152-ФЗ](../compliance/152fz.md), [threat model](security-threat-model.md)

## Сущности

```mermaid
erDiagram
    ORGANIZATION ||--o{ USER : "участники"
    ORGANIZATION ||--o{ DEVICE : "владеет"
    ORGANIZATION ||--o{ SPEAKER_PROFILE : "база голосов (опц.)"
    USER ||--o{ MEETING : "организует"
    DEVICE ||--o{ MEETING : "записывает"
    MEETING ||--o{ AUDIO_SESSION : "потоки-источники"
    MEETING ||--o{ SEGMENT : "стенограмма"
    MEETING ||--o| PROTOCOL : "итог"
    MEETING ||--o{ CONSENT_RECORD : "согласия участников"
    MEETING ||--o{ MARK : "метки «важный момент»"
    SPEAKER_PROFILE ||--o{ SEGMENT : "атрибуция реплик"
    PROTOCOL ||--o{ ACTION_ITEM : "поручения"

    ORGANIZATION {
        uuid id PK
        string name
        string edition "edge|cloud|onprem"
    }
    USER {
        uuid id PK
        string name
        string role "owner|admin|member|viewer"
    }
    DEVICE {
        uuid id PK
        string name "vika-kitchen"
        string tier "thick|thin"
        string token_hash "аутентификация ingest"
    }
    MEETING {
        uuid id PK
        datetime started_at
        datetime ended_at
        string skill "facilitator|transcriber"
        bool private_mode
        string retention_policy
    }
    AUDIO_SESSION {
        uuid id PK
        string source "device|companion|line_in|test"
        int rate
        string wav_path "шифруется at-rest (план)"
        int protocol_version
    }
    SEGMENT {
        uuid id PK
        float start_s
        float end_s
        string text
        string speaker_label "Говорящий N | имя"
        uuid speaker_profile_id FK "nullable"
        float doa_deg "nullable, сектор"
        float asr_confidence
    }
    SPEAKER_PROFILE {
        uuid id PK
        string name
        string role
        blob embedding "БИОМЕТРИЯ — особый режим"
        string scope "meeting_only|org_base"
        uuid consent_id FK
        datetime expires_at "retention"
    }
    CONSENT_RECORD {
        uuid id PK
        uuid meeting_id FK
        string subject_name
        string kind "recording|biometry_storage"
        string evidence "как зафиксировано"
        datetime given_at
        datetime revoked_at "nullable"
    }
    PROTOCOL {
        uuid id PK
        string summary_md
        json decisions
        json talk_time_stats
    }
    ACTION_ITEM {
        uuid id PK
        string assignee
        string task
        date due
        string status
    }
    MARK {
        uuid id PK
        float at_s
        string author
    }
```

## Правила обращения с данными

1. **Биометрия — особый контур.** `SPEAKER_PROFILE.embedding` — биометрические ПДн:
   хранится отдельно от стенограмм, шифруется, имеет обязательный `expires_at` и связь с
   `CONSENT_RECORD`. Scope по умолчанию — `meeting_only` (отпечаток умирает с окончанием
   встречи); `org_base` — только по явному согласию. Открытые правовые вопросы
   (572-ФЗ, уведомление РКН) — [152fz.md](../compliance/152fz.md).
2. **Retention.** У каждой встречи — политика: `keep_all` / `transcript_only`
   (аудио удаляется после чистовой транскрипции) / `ephemeral` (всё удаляется после
   выдачи протокола). Дефолт для приватного режима — `transcript_only` или строже.
   Фоновая задача-чистильщик — обязательная часть EPIC-7.
3. **Шифрование at-rest** аудио и эмбеддингов — требование (пока не реализовано):
   Edge — шифрование раздела данных (LUKS) + ключ вне microSD; Cloud — KMS.
   См. [threat model](security-threat-model.md).
4. **Удаление по запросу субъекта**: каскадное (сегменты → атрибуция → отпечаток),
   фиксируется в журнале аудита.

## Хранилище

- **Скелет (сейчас):** WAV-файлы на диске (`VIKAVOICE_INGEST_DIR`), метаданных нет.
- **EPIC-1..3:** SQLite (по образцу Meetily `backend/app/db.py`) — достаточно для
  одиночного устройства/Edge.
- **EPIC-7 (кабинет, мульти-пользователь):** PostgreSQL + полнотекстовый поиск
  (pg_trgm / tsvector; альтернатива — SQLite FTS5 для Edge). Миграции — alembic.
- Аудио — всегда файлы/объектное хранилище, в БД только пути и метаданные.

## Открытые вопросы

- Формат хранения эмбеддингов (raw float32 vs pgvector) и версии моделей эмбеддера —
  профиль должен знать, какой моделью построен (несовместимость версий).
- Экспортные форматы протокола (docx/pdf) — генерировать на лету или хранить.
- Мульти-тенантность Cloud-редакции (schema-per-org vs row-level) — решить в EPIC-7.
