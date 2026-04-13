from __future__ import annotations

from functools import lru_cache
from io import BytesIO
from pathlib import Path

import numpy as np
from faster_whisper import WhisperModel
from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError

from ..core.config import settings


class TranscriptionError(Exception):
    pass


SUPPORTED_FORMATS = {
    ".wav": "wav",
    ".wave": "wav",
    ".mp3": "mp3",
    ".ogg": "ogg",
    ".oga": "ogg",
    ".flac": "flac",
    ".aiff": "aiff",
    ".aif": "aiff",
    ".m4a": "mp4",
    ".aac": "aac",
}

SUPPORTED_MIME_PREFIXES = (
    "audio/",
    "application/ogg",
    "video/mp4",
)


def _detect_audio_format(filename: str | None, content_type: str | None) -> str:
    if content_type:
        normalized = content_type.lower().split(";")[0].strip()
        if normalized == "audio/mpeg":
            return "mp3"
        if normalized in {"audio/x-wav", "audio/wav"}:
            return "wav"
        if normalized in {"audio/ogg", "application/ogg"}:
            return "ogg"
        if normalized == "audio/flac":
            return "flac"
        if normalized in {"audio/aiff", "audio/x-aiff"}:
            return "aiff"
        if normalized in {"audio/mp4", "audio/x-m4a", "video/mp4"}:
            return "mp4"
        if normalized.startswith(SUPPORTED_MIME_PREFIXES):
            return normalized.split("/", 1)[1]

    suffix = Path(filename or "").suffix.lower()
    if suffix in SUPPORTED_FORMATS:
        return SUPPORTED_FORMATS[suffix]

    return "wav"


def _load_audio_segment(audio_bytes: bytes, audio_format: str) -> AudioSegment:
    try:
        return AudioSegment.from_file(BytesIO(audio_bytes), format=audio_format)
    except CouldntDecodeError as exc:
        raise TranscriptionError("Unsupported or unreadable audio format.") from exc
    except FileNotFoundError as exc:
        raise TranscriptionError(
            "Audio decoding failed because ffmpeg is not installed."
        ) from exc
    except Exception as exc:
        raise TranscriptionError("Could not decode the uploaded audio.") from exc


def _segment_to_float_array(segment: AudioSegment) -> np.ndarray:
    mono = segment.set_channels(1)
    mono = mono.set_frame_rate(16000)
    mono = mono.set_sample_width(2)

    samples = np.array(mono.get_array_of_samples(), dtype=np.float32)
    if samples.size == 0:
        raise TranscriptionError("Audio file is empty.")

    samples /= 32768.0
    return samples


@lru_cache(maxsize=1)
def _get_whisper_model() -> WhisperModel:
    try:
        return WhisperModel(
            settings.whisper_model,
            device=settings.whisper_device,
            compute_type=settings.whisper_compute_type,
        )
    except Exception as exc:
        raise TranscriptionError(
            "Whisper model could not be loaded. Check model files and dependencies."
        ) from exc


def _transcribe_audio_array(audio_array: np.ndarray) -> str:
    model = _get_whisper_model()

    try:
        segments, _info = model.transcribe(
            audio_array,
            vad_filter=True,
        )
        transcript = "".join(segment.text for segment in segments).strip()
        if not transcript:
            raise TranscriptionError("Could not understand the audio.")
        return transcript
    except TranscriptionError:
        raise
    except Exception as exc:
        raise TranscriptionError("Whisper transcription failed.") from exc


def transcribe_audio_bytes(
    audio_bytes: bytes,
    filename: str | None = None,
    content_type: str | None = None,
) -> str:
    if not audio_bytes:
        raise TranscriptionError("Audio file is empty.")

    audio_format = _detect_audio_format(filename, content_type)
    segment = _load_audio_segment(audio_bytes, audio_format)
    audio_array = _segment_to_float_array(segment)
    return _transcribe_audio_array(audio_array)
