from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    user_id: str = Field(..., min_length=1)
    session_id: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    reply: str
    behavior_tags: list[str] = Field(default_factory=list)
    behavior_signals: dict = Field(default_factory=dict)
    recent_messages: int = 0
