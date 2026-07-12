#!/usr/bin/env python3
"""
Клиент-компаньон: захватывает СИСТЕМНЫЙ звук ПК (звук онлайн-встречи) и/или
микрофон и передаёт поток 16 кГц/16 бит моно на ядро по WebSocket.

Программный путь захвата системного звука (см. docs, аналогично Meetily):
  Windows — WASAPI loopback, Linux — PulseAudio monitor, macOS — виртуальное
  устройство (BlackHole) или ScreenCaptureKit. Кроссплатформенно через библиотеку
  `soundcard` (loopback устройства динамика).

Примеры:
  python system_audio_client.py --list
  python system_audio_client.py --server ws://192.168.1.50:8200/ingest --source system
  python system_audio_client.py --source both        # система + микрофон (микс)
  python system_audio_client.py --test                # без звуковых устройств (синус)
"""
import argparse
import os
import asyncio
import math
import struct

RATE = 16000
FRAME_MS = 100
FRAME = RATE * FRAME_MS // 1000  # сэмплов в кадре


def list_devices():
    import soundcard as sc
    print("== Динамики (для loopback системного звука) ==")
    for s in sc.all_speakers():
        print(f"  [spk] {s.name}")
    print("== Микрофоны ==")
    for m in sc.all_microphones(include_loopback=True):
        tag = "loopback" if getattr(m, "isloopback", False) else "mic"
        print(f"  [{tag}] {m.name}")


def open_recorders(source):
    """Возвращает (system_recorder|None, mic_recorder|None) как контекст-объекты soundcard."""
    import soundcard as sc
    sys_rec = mic_rec = None
    if source in ("system", "both"):
        spk = sc.default_speaker()
        # loopback-микрофон, соответствующий динамику по умолчанию
        loop = sc.get_microphone(spk.name, include_loopback=True)
        sys_rec = loop.recorder(samplerate=RATE, channels=1, blocksize=FRAME)
    if source in ("mic", "both"):
        mic = sc.default_microphone()
        mic_rec = mic.recorder(samplerate=RATE, channels=1, blocksize=FRAME)
    return sys_rec, mic_rec


def to_pcm16(float_frame):
    import numpy as np
    x = np.clip(float_frame.reshape(-1), -1.0, 1.0)
    return (x * 32767.0).astype("<i2").tobytes()


async def stream_real(ws, source):
    import numpy as np
    sys_rec, mic_rec = open_recorders(source)
    ctxs = [r for r in (sys_rec, mic_rec) if r]
    for c in ctxs:
        c.__enter__()
    try:
        while True:
            a = sys_rec.record(numframes=FRAME) if sys_rec else None
            b = mic_rec.record(numframes=FRAME) if mic_rec else None
            if a is not None and b is not None:
                mixed = np.clip(a.reshape(-1) + b.reshape(-1), -1.0, 1.0)  # простой микс
            else:
                mixed = (a if a is not None else b).reshape(-1)
            await ws.send(to_pcm16(mixed))
    finally:
        for c in ctxs:
            c.__exit__(None, None, None)


async def stream_test(ws, seconds=3.0):
    """Синтетический синус 440 Гц — проверка сквозного пути без звуковых устройств."""
    total = int(seconds * RATE / FRAME)
    ph = 0.0
    for _ in range(total):
        buf = bytearray()
        for _ in range(FRAME):
            buf += struct.pack("<h", int(0.3 * 32767 * math.sin(ph)))
            ph += 2 * math.pi * 440 / RATE
        await ws.send(bytes(buf))
        await asyncio.sleep(FRAME_MS / 1000)


async def main_async(args):
    import json

    import websockets
    async with websockets.connect(args.server, max_size=None) as ws:
        # заголовок-конфиг СТРОГО первым сообщением (протокол v1, ADR-0009)
        header = {
            "v": 1,
            "rate": RATE,
            "format": "pcm_s16le",
            "channels": 1,
            "source": "test" if args.test else args.source,
        }
        token = args.token or os.environ.get("VIKAVOICE_INGEST_TOKEN")
        if token:
            header["token"] = token
        await ws.send(json.dumps(header))
        print(f">> Подключено к {args.server}. Источник: "
              f"{'test' if args.test else args.source}. Ctrl+C для остановки.")
        if args.test:
            await stream_test(ws)
            print(">> Тест завершён (3 c синуса отправлено).")
        else:
            await stream_real(ws, args.source)


def main():
    p = argparse.ArgumentParser(description="Клиент-компаньон захвата системного звука")
    p.add_argument("--server", default="ws://127.0.0.1:8200/ingest", help="WebSocket ядра")
    p.add_argument("--source", choices=["system", "mic", "both"], default="system")
    p.add_argument("--list", action="store_true", help="показать аудиоустройства")
    p.add_argument("--test", action="store_true", help="синтетический сигнал без устройств")
    p.add_argument("--token", default=None,
                   help="токен устройства (или env VIKAVOICE_INGEST_TOKEN)")
    args = p.parse_args()
    if args.list:
        list_devices()
        return
    try:
        asyncio.run(main_async(args))
    except KeyboardInterrupt:
        print("\n>> Остановлено.")


if __name__ == "__main__":
    main()
