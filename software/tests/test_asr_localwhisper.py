"""Контрактные тесты LocalWhisper против формата вендоренного whisper.cpp-сервера
(Meetily v0.4.0, server.cpp): multipart file + form-поля, verbose_json, error в теле 200.
"""


import httpx
import pytest

from core.asr.base import LocalWhisper, Segment, make_backend

PCM_1S = b"\x01\x00" * 16000  # 1 секунда @ 16 кГц


def _transport(handler):
    return httpx.MockTransport(handler)


def test_verbose_json_segments_parsed():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["content_type"] = request.headers["content-type"]
        captured["body"] = request.read()
        return httpx.Response(
            200,
            json={
                "task": "transcribe",
                "language": "ru",
                "duration": 1.0,
                "text": "привет мир",
                "segments": [
                    {"id": 0, "start": 0.0, "end": 0.6, "text": " привет "},
                    {"id": 1, "start": 0.6, "end": 1.0, "text": "мир"},
                    {"id": 2, "start": 1.0, "end": 1.0, "text": "   "},  # пустой — отбросить
                ],
            },
        )

    w = LocalWhisper(url="http://test/inference", transport=_transport(handler))
    segs = w.transcribe(PCM_1S, rate=16000, lang="ru")
    assert segs == [
        Segment(start=0.0, end=0.6, text="привет"),
        Segment(start=0.6, end=1.0, text="мир"),
    ]
    # multipart с полем file и form-полями протокола сервера
    assert captured["content_type"].startswith("multipart/form-data")
    body = captured["body"]
    assert b'name="file"' in body and b"RIFF" in body  # WAV-обёртка
    for field in (b'name="language"', b'name="response_format"', b'name="diarize"'):
        assert field in body


def test_error_body_raises():
    def handler(request):
        return httpx.Response(200, json={"error": "failed to read audio"})

    w = LocalWhisper(url="http://test/inference", transport=_transport(handler))
    with pytest.raises(RuntimeError, match="failed to read audio"):
        w.transcribe(PCM_1S)


def test_plain_json_fallback_single_segment():
    def handler(request):
        return httpx.Response(200, json={"text": "(speaker 0) привет\n"})

    w = LocalWhisper(url="http://test/inference", transport=_transport(handler))
    segs = w.transcribe(PCM_1S, rate=16000)
    assert len(segs) == 1
    assert segs[0].text == "(speaker 0) привет"
    assert segs[0].end == pytest.approx(1.0)


def test_http_error_raises():
    def handler(request):
        return httpx.Response(500, text="boom")

    w = LocalWhisper(url="http://test/inference", transport=_transport(handler))
    with pytest.raises(httpx.HTTPStatusError):
        w.transcribe(PCM_1S)


def test_make_backend_whisper_kwargs():
    w = make_backend("whisper", url="http://x/inference")
    assert isinstance(w, LocalWhisper)
    assert w.url == "http://x/inference"
