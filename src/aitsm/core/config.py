from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from aitsm.paths import CHROMA_DIR, DATABASE_FILE, ENV_FILE


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_file_encoding="utf-8")

    DATABASE_URL: str = f"sqlite:///{DATABASE_FILE}"
    # Required, no default: a missing key must fail at startup, not run with a known value.
    SECRET_KEY: str = Field(min_length=32)
    LLM_API_URL: str = "http://localhost/v2/llm/invoke"
    LLM_API_KEY: str = ""
    LLM_MODEL_NAME: str = "llama3.2:3b"
    LLM_PROVIDER: str = "bedrock"
    LLM_WORKSPACE_ID: str = ""
    LLM_BACKEND: str = "ollama"
    LLM_TIMEOUT: float = 60.0
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"
    CHROMA_PATH: str = str(CHROMA_DIR)
    SLA_HOURS: dict = {
        "critical": 4,
        "high": 8,
        "medium": 24,
        "low": 72,
    }
    MCP_SYSTEM_USER_ID: str = ""


settings = Settings()
