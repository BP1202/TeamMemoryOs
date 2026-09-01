from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "TeamMemoryOS"
    APP_ENV: str = "development"
    API_V1_PREFIX: str = "/api/v1"

    # JWT Authentication
    JWT_SECRET_KEY: str = "change-this-to-a-long-random-secret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Database
    POSTGRES_USER: str = "teammemory_admin"
    POSTGRES_PASSWORD: str = "changeme"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5433
    POSTGRES_DB: str = "teammemory_os"

    # IBM Granite / Ollama / watsonx.ai
    # Set GRANITE_PROVIDER="ollama" (local Ollama with Granite model), "granite" (watsonx.ai), or "stub" (deterministic fallback)
    GRANITE_PROVIDER: str = "ollama"
    GRANITE_API_KEY: str = ""
    GRANITE_BASE_URL: str = "https://us-south.ml.cloud.ibm.com/ml/v1"
    GRANITE_MODEL_ID: str = "ibm/granite-3-8b-instruct"
    GRANITE_PROJECT_ID: str = ""
    # Ollama settings
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "granite3-dense:2b"
    # Maximum tokens the model may generate in a single response.
    GRANITE_MAX_TOKENS: int = 1024
    # Hard cap on prompt length (characters) before context is trimmed.
    GRANITE_MAX_PROMPT_CHARS: int = 8000

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()