from pydantic import BaseModel, Field
from fastapi import APIRouter, Body, HTTPException
from fastapi.responses import Response

from ...services.tts_service import TTSGenerationError, text_to_speech_audio

router = APIRouter(prefix="/tts", tags=["tts"])


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1)
    lang: str = Field(default="en")


@router.post("/speak")
def speak_text(
    payload: TTSRequest = Body(...),
) -> Response:
    try:
        audio_bytes = text_to_speech_audio(payload.text, lang=payload.lang)
        return Response(content=audio_bytes, media_type="audio/mpeg")
    except TTSGenerationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Neura could not generate speech output.",
        )
