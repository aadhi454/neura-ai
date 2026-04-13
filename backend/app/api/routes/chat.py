from fastapi import APIRouter, HTTPException

from ...schemas import ChatRequest, ChatResponse
from ...services.chat_service import process_chat_message

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    try:
        return process_chat_message(payload.user_id, payload.session_id, payload.message)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Neura hit a temporary issue while processing your message.",
        )
