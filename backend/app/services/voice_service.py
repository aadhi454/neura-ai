from __future__ import annotations

from fastapi import UploadFile

from ..schemas import ChatResponse
from .chat_service import process_chat_message
from .transcription_service import TranscriptionError, transcribe_audio_bytes
from .tts_service import text_to_speech_audio


async def transcribe_voice_upload(file: UploadFile) -> str:
    audio_bytes = await file.read()
    return transcribe_audio_bytes(audio_bytes, file.filename, file.content_type)


async def process_voice_chat_upload(
    user_id: str,
    session_id: str,
    file: UploadFile,
) -> ChatResponse:
    transcript = await transcribe_voice_upload(file)
    return process_chat_message(user_id, session_id, transcript)


async def process_voice_chat_audio_upload(
    user_id: str,
    session_id: str,
    file: UploadFile,
    lang: str = "en",
) -> bytes:
    try:
        transcript = await transcribe_voice_upload(file)
        chat_response = process_chat_message(user_id, session_id, transcript)
        return text_to_speech_audio(chat_response.reply, lang=lang)
    except TranscriptionError:
        return text_to_speech_audio("Didn’t catch that properly… say it again?", lang=lang)
