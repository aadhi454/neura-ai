from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

from ...schemas import ChatResponse
from ...services.tts_service import TTSGenerationError
from ...services.voice_service import (
    process_voice_chat_audio_upload,
    process_voice_chat_upload,
    transcribe_voice_upload,
)
from ...services.transcription_service import TranscriptionError

router = APIRouter(prefix="/voice", tags=["voice"])


@router.post("/transcribe")
async def transcribe_voice(
    file: UploadFile = File(...),
) -> dict:
    try:
        transcript = await transcribe_voice_upload(file)
        return {"text": transcript}
    except TranscriptionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Neura could not process the audio file.") from exc


@router.post("/chat", response_model=ChatResponse)
async def voice_chat(
    user_id: str = Form(...),
    session_id: str = Form(...),
    file: UploadFile = File(...),
) -> ChatResponse:
    try:
        return await process_voice_chat_upload(user_id, session_id, file)
    except TranscriptionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Neura could not process the audio chat request.",
        )


@router.post("/chat-audio")
async def voice_chat_audio(
    user_id: str = Form(...),
    session_id: str = Form(...),
    file: UploadFile = File(...),
    lang: str = Form(default="en"),
) -> Response:
    try:
        audio_bytes = await process_voice_chat_audio_upload(user_id, session_id, file, lang=lang)
        return Response(content=audio_bytes, media_type="audio/mpeg")
    except TTSGenerationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Neura could not complete the voice chat pipeline.",
        )
