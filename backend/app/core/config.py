import os

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

if load_dotenv is not None:
    load_dotenv()


class Settings:
    app_name: str = os.getenv("APP_NAME", "Neura")
    database_path: str = os.getenv("DATABASE_PATH", "memory.db")
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_base_url: str = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
    groq_model: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
    recent_message_limit: int = int(os.getenv("RECENT_MESSAGE_LIMIT", "6"))
    response_max_lines: int = int(os.getenv("RESPONSE_MAX_LINES", "2"))
    response_max_chars: int = int(os.getenv("RESPONSE_MAX_CHARS", "220"))
    response_max_tokens: int = int(os.getenv("RESPONSE_MAX_TOKENS", "80"))
    max_message_chars: int = int(os.getenv("MAX_MESSAGE_CHARS", "4000"))
    whisper_model: str = os.getenv("WHISPER_MODEL", "small")
    whisper_device: str = os.getenv("WHISPER_DEVICE", "cpu")
    whisper_compute_type: str = os.getenv("WHISPER_COMPUTE_TYPE", "int8")


settings = Settings()
