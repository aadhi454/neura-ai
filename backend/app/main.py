from fastapi import FastAPI

from .api.routes.chat import router as chat_router
from .api.routes.tts import router as tts_router
from .api.routes.voice import router as voice_router
from .core.config import settings
from .db.database import init_db

app = FastAPI(title=settings.app_name)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/")
def home() -> dict[str, str]:
    return {"message": "Neura is alive 🚀"}


app.include_router(chat_router)
app.include_router(voice_router)
app.include_router(tts_router)
