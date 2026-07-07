# Стартовый каркас продукта (форк-основа)

Ядро продукта записи и транскрибации переговоров: берём программную базу из
**Meetily** (MIT), строим вокруг неё наш звуковой тракт, запоминание голоса, три
редакции и оба пути захвата системного звука.

Полная карта переиспользования — в [`REUSE_MAP.md`](REUSE_MAP.md).
Атрибуция сторонних лицензий — в [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

## Структура
```
meeting-device/
├─ REUSE_MAP.md               # что откуда берём (главный документ)
├─ THIRD_PARTY_NOTICES.md     # атрибуция MIT (Meetily) и апстрима
├─ docker-compose.yml         # ядро -> Edge/Cloud/On-prem через env
├─ scripts/
│  └─ vendor_meetily.sh       # подтягивает нужные части Meetily в core/vendor/
├─ core/
│  ├─ api/ingest_ws.py        # приём аудио по WebSocket (РАБОТАЕТ, протестировано)
│  ├─ asr/base.py             # подключаемый ASR-бэкенд (интерфейс)
│  ├─ voice_enrollment/enroll.py  # запоминание голоса + именование (наша фича)
│  ├─ mic_array/README.md     # интерфейс к аппаратному массиву (beamforming/DOA)
│  └─ vendor/                 # сюда vendor_meetily.sh кладёт код Meetily
├─ companion-client/          # ПРОГРАММНЫЙ захват системного звука (клиент)
│  └─ system_audio_client.py  # РАБОТАЕТ (проверено в режиме --test)
└─ docs/
   └─ hardware_line_in.md     # АППАРАТНЫЙ захват системного звука (проводом)
```

## Как сделать настоящий форк (на вашем GitHub)
Это каркас-обёртка; сам Meetily остаётся отдельным апстримом, чтобы получать обновления.
```bash
# 1) форк Meetily на свой аккаунт (через веб или gh cli)
gh repo fork Zackriya-Solutions/meetily --clone=false

# 2) в этом репозитории подтянуть нужные части (в core/vendor/meetily):
bash scripts/vendor_meetily.sh
# при желании закрепить версию:  MEETILY_REF=v0.4.0 bash scripts/vendor_meetily.sh
```

## Захват системного звука — два пути
- **Программный** — `companion-client/` (клиент на ПК шлёт звук в ядро). Windows: WASAPI
  loopback, Linux: Pulse monitor, macOS: BlackHole/ScreenCaptureKit. Проверено сквозным
  тестом.
- **Аппаратный** — `docs/hardware_line_in.md` (звук ПК проводом в линейный вход устройства).

## Быстрый прогон (что уже работает)
```bash
# ядро: приём аудио
cd meeting-device && PYTHONPATH=. uvicorn core.api.ingest_ws:app --port 8200
# в другом окне: клиент шлёт тестовый сигнал
python companion-client/system_audio_client.py --test
# в /tmp/ingest_sessions появится WAV принятого потока
```

## Что ещё построить (см. REUSE_MAP)
Звуковой тракт массива (beamforming/DOA), эмбеддер голоса для enrollment, веб-кабинет,
локализация RU, слой 152-ФЗ/44-ФЗ, привязка whisper/parakeet к `core/asr/base.py`.
