from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    DATABASE_URL: str = "sqlite:///./aitsm.db"
    SECRET_KEY: str = "change-me-in-production"
    LLM_API_URL: str = "http://localhost"
    LLM_API_KEY: str = ""
    CHROMA_PATH: str = "./chroma_data"


settings = Settings()
