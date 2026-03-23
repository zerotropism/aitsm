from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    DATABASE_URL: str = "sqlite:///./aitsm.db"
    SECRET_KEY: str = "change-me-in-production"
    LLM_API_URL: str = "http://localhost/v2/llm/invoke"
    LLM_API_KEY: str = ""
    LLM_MODEL_NAME: str = "mistral.mistral-7b-instruct-v0:2"
    LLM_PROVIDER: str = "bedrock"
    LLM_WORKSPACE_ID: str = ""
    CHROMA_PATH: str = "./chroma_data"
    SLA_HOURS: dict = {
        "critical": 1 / 60,  # 1min for testing, change to proper value for production
        "high": 8,
        "medium": 24,
        "low": 72,
    }


settings = Settings()
