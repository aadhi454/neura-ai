from __future__ import annotations

import io

from gtts import gTTS


class TTSGenerationError(Exception):
    pass


def text_to_speech_audio(text: str, lang: str = "en") -> bytes:
    cleaned_text = " ".join((text or "").strip().split())

    if not cleaned_text:
        raise TTSGenerationError("Text is empty.")

    try:
        tts = gTTS(text=cleaned_text, lang=lang)

        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)

        audio_buffer.seek(0)

        return audio_buffer.read()

    except Exception as exc:
        raise TTSGenerationError(f"TTS failed: {exc}") from exc
