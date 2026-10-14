import re
import wave

import batch_runner


def test_espeak_audio_targets_exact_format_duration(tmp_path, monkeypatch):
    monkeypatch.setattr(batch_runner, "TEMP_AUDIO", tmp_path)
    calls = []

    def fake_run(command, check):
        calls.append(command)
        if command[0] == "espeak-ng":
            source_path = command[command.index("-w") + 1]
            with wave.open(source_path, "wb") as source:
                source.setnchannels(1)
                source.setsampwidth(2)
                source.setframerate(44100)
                source.writeframes(b"\x00\x00" * (54 * 44100))
        else:
            output_path = command[-1]
            target = float(re.search(r"atrim=duration=([0-9.]+)", command[command.index("-af") + 1]).group(1))
            with wave.open(output_path, "wb") as voice:
                voice.setnchannels(1)
                voice.setsampwidth(2)
                voice.setframerate(44100)
                voice.writeframes(b"\x00\x00" * int(target * 44100))

    monkeypatch.setattr(batch_runner.subprocess, "run", fake_run)
    script = " ".join(["Explain"] * 130)
    voice, pad, duration = batch_runner._synthesize_espeak_for_row(
        {"orientation": "vertical", "audio_script": script},
        "test-short",
    )

    assert duration == 55.0
    assert len(calls) == 2
    assert calls[0][0] == "espeak-ng"
    assert calls[1][0] == "ffmpeg"
    with wave.open(voice, "rb") as result:
        assert result.getnframes() / result.getframerate() == 55.0
    with wave.open(pad, "rb") as result:
        assert result.getnframes() / result.getframerate() == 55.0
    assert not list(tmp_path.glob("*_espeak_*"))
